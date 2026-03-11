from fastapi import APIRouter,HTTPException,Depends,Form
from .resume_parse import ResumeParseService
from fastapi import UploadFile, File
from app.utils.file_handler import FileHandler
from app.DB.mongodb.mongodb import MongoDB
from typing import Optional

router = APIRouter()


@router.post("/resume-parse")
async def resume_parse(
     user_id: str = Form(...),             
     resume_text: Optional[str] = Form(None),
     file: Optional[UploadFile] = File(None),  
):
     try:
          if resume_text:
               result = await ResumeParseService().parse_resume(resume_text)
               return result

          if not file:
               raise HTTPException(status_code=400, detail="Either resume_text or a file must be provided")

          file_extension = file.filename.split(".")[-1]
          extracted_text = await FileHandler.file_handler(await file.read(), file_extension)
          print(extracted_text)
          result = await ResumeParseService().parse_resume(extracted_text)
          return result

     except HTTPException:
          raise
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
'''
@router.put("/upsert_skill")
async def upsert_skill(
     user_id:str,
     skill:Skill,
     db:MongoDB = Depends(MongoDB)
):
     try:
          result = await db.smart_upsert_skill(user_id,skill)
          return result
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))

@router.get("/resume-parse/{user_id}")
async def get_resume_parse_info(user_id:str,db:MongoDB = Depends(MongoDB)):
     try:
          result = await db.get_resume_by_user_id(user_id)
          return result
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))

@router.get("/skill/{user_id}")
async def get_skill(user_id:str,db:MongoDB = Depends(MongoDB)):
     try:
          result = await db.get_skill(user_id)
          return result
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))


'''