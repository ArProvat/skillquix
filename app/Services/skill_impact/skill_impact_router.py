from fastapi import APIRouter,HTTPException,Depends,Form
from .skill_impact import SkillImpact
from typing import Optional
from app.moduls.auth.auth import verify_token


router = APIRouter()


@router.post("/skill-impact")
async def skill_impact(
     skill:Optional[str] = Form(None),
     user = Depends(verify_token)
):
     try:
          result = await SkillImpact().get_skill_impact(skill)
          return result

     except HTTPException:
          raise
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))