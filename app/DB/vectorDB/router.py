from fastapi import APIRouter, HTTPException, Depends, Form
from .vectordb import  upsert_gig_embedding, upsert_resume_embedding
from app.Services.match_gig.match_gig import MatchGig
from .schema import UpsertEmbeddingRequest,UpsertResumeRequest
router = APIRouter()

@router.post("/upsert_gig_embedding")
async def gig_embedding(
     gig_id: str,
     body: UpsertEmbeddingRequest
):
     try:
          await upsert_gig_embedding(gig_id, body.embedding)   # ← calls qdrant, not itself
          user_id = MatchGig().notify_matched_users_for_gig(body.embedding)
          return {"message": "Gig embedding upserted successfully", "user_id": user_id}
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