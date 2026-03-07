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
VECTOR_SIZE       = 1024  #BAAI/bge-base-en-v1.5


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


from qdrant_client.models import PointStruct, Distance, VectorParams

async def upsert_gig_embedding(gig_id: str, embedding: list):
     await client.upsert(
          collection_name=GIG_COLLECTION,
          points=[
               PointStruct(
                    id=_id_to_int(gig_id),
                    vector=embedding,
                    payload={"mongo_id": gig_id}
               )
          ]
     )


async def upsert_resume_embedding(user_id: str, embedding: list):
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




async def search_similar_gigs(embedding: list, limit: int) -> list[dict]:
     results = await client.query_points(
          collection_name=GIG_COLLECTION,
          query=embedding,
          limit=limit,
          score_threshold=0.50,
     )
     return [
          {
               "gig_id": hit.payload["mongo_id"],
               "score": hit.score
          }
          for hit in results.points      # ← .points not direct iteration
     ]


async def search_similar_resumes(gig_embedding: list, limit: int = 50) -> list[str]:
     results = await client.query_points(
          collection_name=RESUME_COLLECTION,
          query=gig_embedding,
          limit=limit,
          score_threshold=0.60,
     )
     return [hit.payload["mongo_id"] for hit in results.points]

def _id_to_int(mongo_id: str) -> int:
     """Safe conversion — works for both ObjectId strings and plain strings."""
     try:
          return int(mongo_id, 16) % (2 ** 63)       # ObjectId hex string
     except ValueError:
          return abs(hash(mongo_id)) % (2 ** 63)     # fallback for non-hex ids like "3333"