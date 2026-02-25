from fastapi import APIRouter,HTTPException
from .skill_impact import SkillImpact
from .skill_impact_schema import SkillImpactSchema

router = APIRouter()


@router.post("/skill-impact" ,response_model=SkillImpactSchema)
async def skill_impact(
     skill:str,
):
     try:
          result = await SkillImpact().get_skill_impact(skill)
          return result

     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))