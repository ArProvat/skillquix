# qdrant_service.py
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import os

QDRANT_HOST   = os.getenv("QDRANT_HOST", "187.77.210.157")
QDRANT_PORT   = int(os.getenv("QDRANT_PORT", 6333))
VECTOR_SIZE   = 768  # BAAI/bge-base-en-v1.5

GIG_COLLECTION    = "gigs"
RESUME_COLLECTION = "resumes"
MENTOR_COLLECTION = "mentors"

ALL_COLLECTIONS = [GIG_COLLECTION, RESUME_COLLECTION, MENTOR_COLLECTION]

client = AsyncQdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


# ------------------------------------------------------------------ #
#  Collection bootstrap                                                #
# ------------------------------------------------------------------ #

async def create_collections():
     """
     Run on startup.
     - Creates the collection if it doesn't exist.
     - Recreates it if the stored vector dimension doesn't match VECTOR_SIZE.
     """
     for name in ALL_COLLECTIONS:
          exists = await client.collection_exists(name)

          if exists:
               info      = await client.get_collection(name)
               stored_dim = info.config.params.vectors.size  # actual dim on disk

               if stored_dim == VECTOR_SIZE:
                    print(f"⏭️  '{name}' exists with correct dim={VECTOR_SIZE}, skipping")
                    continue

               # Dim mismatch — must recreate
               print(
                    f"⚠️  '{name}' has dim={stored_dim}, expected {VECTOR_SIZE}. "
                    f"Recreating collection..."
               )
               await client.delete_collection(name)

          await client.create_collection(
               collection_name=name,
               vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
          )
          print(f"✅ '{name}' created with dim={VECTOR_SIZE}")


# ------------------------------------------------------------------ #
#  Upsert helpers                                                      #
# ------------------------------------------------------------------ #

async def _upsert(collection: str, doc_id: str, embedding: list) -> None:
     """Single upsert implementation reused by all three helpers."""
     if len(embedding) != VECTOR_SIZE:
          raise ValueError(
               f"Embedding dim mismatch: expected {VECTOR_SIZE}, got {len(embedding)}"
          )
     await client.upsert(
          collection_name=collection,
          points=[
               PointStruct(
                    id=_id_to_int(doc_id),
                    vector=embedding,
                    payload={"mongo_id": doc_id},
               )
          ],
     )


async def upsert_gig_embedding(gig_id: str, embedding: list) -> None:
     await _upsert(GIG_COLLECTION, gig_id, embedding)


async def upsert_resume_embedding(user_id: str, embedding: list) -> None:
     await _upsert(RESUME_COLLECTION, user_id, embedding)


async def upsert_mentor_embedding(mentor_id: str, embedding: list) -> None:
     await _upsert(MENTOR_COLLECTION, mentor_id, embedding)


# ------------------------------------------------------------------ #
#  Search helpers                                                      #
# ------------------------------------------------------------------ #

async def search_similar_gigs(embedding: list, limit: int = 10) -> list[dict]:
     results = await client.query_points(
          collection_name=GIG_COLLECTION,
          query=embedding,
          limit=limit,
          score_threshold=0.50,
     )
     return [{"gig_id": hit.payload["mongo_id"], "score": hit.score}
               for hit in results.points]


async def search_similar_resumes(gig_embedding: list, limit: int = 50) -> list[str]:
     results = await client.query_points(
          collection_name=RESUME_COLLECTION,
          query=gig_embedding,
          limit=limit,
          score_threshold=0.60,
     )
     return [hit.payload["mongo_id"] for hit in results.points]


async def search_similar_mentors(embedding: list, limit: int = 10) -> list[dict]:
     results = await client.query_points(
          collection_name=MENTOR_COLLECTION,
          query=embedding,
          limit=limit,
          score_threshold=0.70,
     )
     return [{"mentor_id": hit.payload["mongo_id"], "score": hit.score}
               for hit in results.points]


# ------------------------------------------------------------------ #
#  Utility                                                             #
# ------------------------------------------------------------------ #

def _id_to_int(mongo_id: str) -> int:
     try:
          return int(mongo_id, 16) % (2 ** 63)   # ObjectId hex string
     except ValueError:
          return abs(hash(mongo_id)) % (2 ** 63) # fallback for non-hex ids