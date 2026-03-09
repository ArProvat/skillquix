

from fastapi import APIRouter, HTTPException, Depends, Form
from .mentor_match import MentorMatch
from .mentor_match_schema import MentorMatchRequest
import asyncio
router = APIRouter()

@router.post("/mentor_match")
async def mentor_match(
     user_id: str,
     gig_id :str
):
     try:
     
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))