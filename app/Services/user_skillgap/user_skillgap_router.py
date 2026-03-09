from fastapi import APIRouter, HTTPException, Depends, Form
from .user_skillgap import UserSkillGap
from .user_skillgap_schema import UserSkillGapRequest
import asyncio
router = APIRouter()

@router.post("/user_skillgap")
async def user_skillgap(
     user_id: str,
     gig_id :str
):
     try:
          
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))