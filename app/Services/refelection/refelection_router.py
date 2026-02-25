from fastapi import APIRouter, HTTPException
from .refelection import refelection
from .refelection_schema import refelectionResponse

router = APIRouter()
refelection_instance = refelection()

@router.get("/refelection")
async def get_refelection(work_text: str, reasoning_text: str, impact_text: str):
     try:
          response = await refelection_instance.ger_response(work_text, reasoning_text, impact_text)
          return response
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))