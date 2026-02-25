from fastapi import APIRouter, HTTPException, Depends, Form
from .match_gig import MatchGig


router = APIRouter()


@router.post("/get-embedding")
async def match_gig(
     text: str,
):
     try:
          result = await MatchGig().get_embedding(text)
          return result

     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
