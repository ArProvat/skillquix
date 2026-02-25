from fastapi import APIRouter, Depends, HTTPException
from .recommend_skill import RecommendSkillAgent
from app.DB.mongodb.mongodb import MongoDB

router = APIRouter()


@router.post("/recommend-skill/{user_id}")
async def recommend_skill(user_id: str, db: MongoDB = Depends(MongoDB)):
     try:
          agent = RecommendSkillAgent()
          result = await agent.get_response(user_id)
          return {
               "message": "Recommended skill successfully",
               "recommended_skills": result.model_dump()
          }
     except ValueError as e:
          raise HTTPException(status_code=404, detail=str(e))
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))