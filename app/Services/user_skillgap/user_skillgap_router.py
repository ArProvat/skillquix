from fastapi import APIRouter, HTTPException, Depends, Form
from .user_skillgap import skillgap_service
from .user_skillgap_schema import UserSkillGapRequest
from app.DB.mongodb.mongodb import MongoDB
router = APIRouter()
skillgap =skillgap_service()
mongodb = MongoDB()

@router.get("/user_skillgap")
async def user_skillgap(
     user_id: str,
     gig_id :str
):
     try:
          result = await mongodb.get_skill_gap(user_id, gig_id)
          if result:
               return result
          else:
               result = await skillgap.get_response(user_id, gig_id)
               await mongodb.insert_skill_gap(user_id, gig_id, result)
          return result

     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))

