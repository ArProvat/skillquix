from fastapi import APIRouter, Depends, HTTPException
from .recommend_skill import RecommendSkillAgent
from app.DB.mongodb.mongodb import MongoDB

router = APIRouter()

@router.post("/recommend-skill/{user_id}")
async def recommend_skill(user_id: str, db: MongoDB = Depends(MongoDB)):
     try:
          result = await RecommendSkillAgent().get_response(user_id)
          return {"message":"Recommended skill inserted successfully","recommended_skill_id":str(result.get("_id"))}
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))