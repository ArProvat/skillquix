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

async def recreate_collections():
     """Drop and recreate collections with correct dimensions."""
     for name in [GIG_COLLECTION, RESUME_COLLECTION]:
          exists = await client.collection_exists(name)
          if exists:
               await client.delete_collection(name)
               print(f"🗑️  Deleted old collection '{name}'")

          await client.create_collection(
               collection_name=name,
               vectors_config=VectorParams(
                    size=VECTOR_SIZE,        # ← 768
                    distance=Distance.COSINE
               )
          )
          print(f"✅ Created '{name}' with dim={VECTOR_SIZE}")


async def create_collections():
     """Safe create — skips if exists."""
     for name in [GIG_COLLECTION, RESUME_COLLECTION]:
          exists = await client.collection_exists(name)
          if not exists:
               await client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
               )
               print(f"✅ Qdrant collection '{name}' created with dim={VECTOR_SIZE}")
          else:
               print(f"⏭️  '{name}' already exists")

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


'''async def upsert_resume_embedding(user_id: str, embedding: list) -> None:
     await _upsert(RESUME_COLLECTION, user_id, embedding)
'''

async def upsert_mentor_embedding(mentor_id: str, embedding: list) -> None:
     await _upsert(MENTOR_COLLECTION, mentor_id, embedding)


# ------------------------------------------------------------------ #
#  Search helpers                                                      #
# ------------------------------------------------------------------ #
# vectordb.py

# vectordb.py — add verification to upsert

async def upsert_resume_embedding(user_id: str, embedding: list):
     point_id = _id_to_int(user_id)
     print(f"[Qdrant] Upserting resume — user_id: {user_id}, point_id: {point_id}, dim: {len(embedding)}")

     await client.upsert(
          collection_name=RESUME_COLLECTION,
          points=[
               PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={"mongo_id": user_id}
               )
          ]
     )

     # ✅ Verify immediately after upsert
     verify = await client.retrieve(
          collection_name=RESUME_COLLECTION,
          id=[point_id],
          with_vectors=False,
          with_payload=True,
     )
     print(f"[Qdrant] Verify after upsert: {verify}")
     return point_id


async def get_embedding_by_id(collection_name: str, mongo_id: str) -> list | None:
     point_id = _id_to_int(mongo_id)
     print(f"[Qdrant] Retrieving — mongo_id: {mongo_id}, point_id: {point_id}, collection: {collection_name}")

     results = await client.retrieve(
          collection_name=collection_name,
          id=[point_id],
          with_vectors=True,
          with_payload=True,
     )
     print(f"[Qdrant] Retrieve results: {results}")
     return results[0].vector if results else None


# Convenience wrappers
async def get_gig_embedding(gig_id: str) -> list | None:
     return await get_embedding_by_id(GIG_COLLECTION, gig_id)

async def get_resume_embedding(user_id: str) -> list | None:
     return await get_embedding_by_id(RESUME_COLLECTION, user_id)

async def search_similar_gigs(embedding: list, limit: int = 10) -> list[dict]:
     results = await client.query_points(
          collection_name=GIG_COLLECTION,
          query=embedding,
          limit=limit,
          score_threshold=0.50,
     )
     return [{"gig_id": hit.payload["mongo_id"], "score": hit.score}
               for hit in results.points]


async def search_similar_resumes(gig_embedding: list, limit: int = 50) -> list[dict]:
     results = await client.query_points(
          collection_name=RESUME_COLLECTION,
          query=gig_embedding,
          limit=limit,
          score_threshold=0.60,
     )
     return [
          {
               "user_id": hit.payload["mongo_id"],  # ← dict not string
               "score":   hit.score,
          }
          for hit in results.points
     ]


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