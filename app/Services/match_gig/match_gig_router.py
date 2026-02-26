from fastapi import APIRouter, HTTPException, Depends, Form
from .match_gig import MatchGig


router = APIRouter()
match_gig=MatchGig()

@router.post("/get-embedding")
async def match_gig(
     text: str,
):
     try:
          result = await match_gig.get_embedding(text)
          return result

     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
@router.get("/gigs/similar/{user_id}")
async def get_similar_gigs(user_id: str):
     gigs = await match_gig.get_similar_gigs(user_id)
     return {"user_id": user_id, "total": len(gigs), "gigs": gigs}