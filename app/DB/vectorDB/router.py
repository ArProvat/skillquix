from fastapi import APIRouter, HTTPException, Depends, Form
from .vectordb import  upsert_gig_embedding, upsert_resume_embedding

router = APIRouter()

@router.post("/upsert_gig_embedding")
async def upsert_gig_embedding(
     gig_id: str,
     embedding: list,
):
     try:
          await upsert_gig_embedding(gig_id, embedding)
          return {"message": "Gig embedding upserted successfully"}
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))

@router.post("/upsert_resume_embedding")
async def upsert_resume_embedding(
     user_id: str,
     embedding: list,
):
     try:
          await upsert_resume_embedding(user_id, embedding)
          return {"message": "Resume embedding upserted successfully"}
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
