from fastapi import APIRouter,HTTPException,Depends,Form
from .match_gig import MatchGig
from typing import Optional
from app.moduls.auth.auth import verify_token


router = APIRouter()


@router.post("/get-embedding")
async def match_gig(
     text:Optional[str] = Form(None),
     user = Depends(verify_token)
):
     try:
          result = await MatchGig().get_embedding(text)
          return result

     except HTTPException:
          raise
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))