from fastapi import APIRouter, HTTPException
from .refelection import refelection
from .refelection_schema import refelectionResponse

router = APIRouter()


@router.post("/refelection", response_model=refelectionResponse)
async def refelection(work_text: str, reasoning_text: str, impact_text: str):
     try:
          refelection = refelection()
          response = await refelection.refelection(work_text, reasoning_text, impact_text)
          return response
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))