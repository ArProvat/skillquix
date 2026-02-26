# qdrant_service.py
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance, VectorParams,
    PointStruct, SearchRequest
)
import os

QDRANT_HOST = os.getenv("QDRANT_HOST", "187.77.210.157")  # your VPS IP
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

client = AsyncQdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

GIG_COLLECTION    = "gigs"
RESUME_COLLECTION = "resumes"
VECTOR_SIZE       = 384  # all-MiniLM-L6-v2


async def create_collections():
     """Run once on startup — safe to re-run, skips if exists."""
     for name in [GIG_COLLECTION, RESUME_COLLECTION]:
          exists = await client.collection_exists(name)
          if not exists:
               await client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                         size=VECTOR_SIZE,
                         distance=Distance.COSINE
                    )
               )
               print(f"✅ Qdrant collection '{name}' created")
          else:
               print(f"⏭️  Qdrant collection '{name}' already exists")


async def upsert_gig_embedding(gig_id: str, embedding: list):
     """Called by backend after saving a new gig with its embedding."""
     await client.upsert(
          collection_name=GIG_COLLECTION,
          points=[
               PointStruct(
                    id=_id_to_int(gig_id),
                    vector=embedding,
                    payload={"mongo_id": gig_id}  # keep reference back to MongoDB
               )
          ]
     )


async def upsert_resume_embedding(user_id: str, embedding: list):
     """Called by backend after saving/updating a resume."""
     await client.upsert(
          collection_name=RESUME_COLLECTION,
          points=[
               PointStruct(
                    id=_id_to_int(user_id),
                    vector=embedding,
                    payload={"mongo_id": user_id}
               )
          ]
     )


async def search_similar_gigs(resume_embedding: list, limit: int = 100) -> list[str]:
     """Returns list of MongoDB gig_ids sorted by similarity."""
     results = await client.search(
          collection_name=GIG_COLLECTION,
          query_vector=resume_embedding,
          limit=limit,
          score_threshold=0.45,  # tune this — ignore weak matches
     )
     return [r.payload["mongo_id"] for r in results]


async def search_similar_resumes(gig_embedding: list, limit: int = 50) -> list[str]:
     """Used for notifications — find users matching a new gig."""
     results = await client.search(
          collection_name=RESUME_COLLECTION,
          query_vector=gig_embedding,
          limit=limit,
          score_threshold=0.60,
     )
     return [r.payload["mongo_id"] for r in results]


def _id_to_int(mongo_id: str) -> int:
     """Qdrant needs integer IDs — convert MongoDB ObjectId string to int."""
     return int(mongo_id, 16) % (2**63)  # safe positive int64