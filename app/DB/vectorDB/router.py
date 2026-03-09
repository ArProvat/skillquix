from fastapi import APIRouter, HTTPException, Depends, Form
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
     ):
     try:
          qdrant_result, matched_user_ids = await asyncio.gather(
               upsert_gig_embedding(gig_id, body.embedding),
               MatchGig().notify_matched_users_for_gig(gig_id, body.embedding),
          )
          return {
               "message":          "Gig embedding upserted successfully",
               "matched_users":    len(matched_user_ids),
               "matched_user_ids": matched_user_ids,
          }
     except HTTPException:
          raise
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