from fastapi import APIRouter, HTTPException, Depends, Form ,BackgroundTasks
from .vectordb import  upsert_gig_embedding, upsert_resume_embedding,upsert_mentor_embedding
from app.Services.match_gig.match_gig import MatchGig
from .schema import UpsertEmbeddingRequest,UpsertResumeRequest
import asyncio
router = APIRouter()

# router — use singleton, fix return value
@router.post("/upsert_gig_embedding")
async def gig_embedding(
     gig_id: str,
     body: UpsertEmbeddingRequest,
     background_tasks: BackgroundTasks):
     try:
          qdrant_result = await upsert_gig_embedding(gig_id, body.embedding)
     
          background_tasks.add_task(
               MatchGig().notify_matched_users_for_gig,
               gig_id,
               body.embedding,
          )
          return {
               "message": "Gig embedding upserted successfully",
               }
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))


@router.post("/upsert_resume_embedding")
async def resume_embedding(
     user_id: str,
     body: UpsertResumeRequest
):
     try:
          await upsert_resume_embedding(user_id, body.embedding)  # ← calls qdrant, not itself
          return {"message": "Resume embedding upserted successfully"}
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))

@router.post("/upsert_mentor_embedding")
async def mentor_embedding(
     mentor_id: str,
     body: UpsertEmbeddingRequest
):
     try:
          await upsert_mentor_embedding(mentor_id, body.embedding)  # ← calls qdrant, not itself
          return {"message": "Mentor embedding upserted successfully"}
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))

# router
from app.DB.vectorDB.vectordb import recreate_collections

@router.post("/admin/reset-qdrant")
async def reset_qdrant():
     """
     Run ONCE after switching embedding model.
     Deletes old collections + recreates with correct dimensions.
     Then re-index all gigs.
     """
     await recreate_collections()
     return {"message": "Qdrant collections recreated with dim=768"}

from app.DB.vectorDB.vectordb import get_embedding_by_id
@router.get("/debug/qdrant-embedding/{collection}/{mongo_id}")
async def debug_get_embedding(collection: str, mongo_id: str):

     embedding = await get_embedding_by_id(collection, mongo_id)

     if not embedding:
          return {"found": False, "mongo_id": mongo_id, "collection": collection}

     return {
          "found":      True,
          "mongo_id":   mongo_id,
          "collection": collection,
          "dimensions": len(embedding),
          "preview":    embedding[:5],   # first 5 values only
     }

@router.get("/debug/qdrant-full/{user_id}")
async def debug_qdrant_full(user_id: str):
     from app.DB.vectorDB.vectordb import client, RESUME_COLLECTION, _id_to_int

     point_id = _id_to_int(user_id)

     # 1. Check collection info
     try:
          info = await client.get_collection(RESUME_COLLECTION)
          collection_info = {
               "name":       RESUME_COLLECTION,
               "dim":        info.config.params.vectors.size,
               "points":     info.points_count,
          }
     except Exception as e:
          return {"step": "FAILED at collection check", "error": str(e)}

     # 2. Check point exists
     try:
          results = await client.retrieve(
               collection_name=RESUME_COLLECTION,
               ids=[point_id],
               with_vectors=False,
               with_payload=True,
          )
          point_exists = len(results) > 0
          payload      = results[0].payload if results else None
     except Exception as e:
          return {"step": "FAILED at retrieve", "error": str(e)}

     # 3. Scroll all points — see what's actually stored
     try:
          scroll_result = await client.scroll(
               collection_name=RESUME_COLLECTION,
               limit=10,
               with_payload=True,
               with_vectors=False,
          )
          all_points = [
               {"id": p.id, "payload": p.payload}
               for p in scroll_result[0]
          ]
     except Exception as e:
          all_points = [{"error": str(e)}]

     return {
          "user_id":        user_id,
          "point_id":       point_id,
          "collection":     collection_info,
          "point_exists":   point_exists,
          "payload":        payload,
          "all_points_in_collection": all_points,  # ← see what's actually stored
     }