from fastapi import APIRouter,HTTPException,Depends
from .resume_parse import ResumeParseService
from fastapi import UploadFile, File
from app.utils.file_handler import FileHandler
from app.DB.mongodb.mongodb import MongoDB
from .resume_parse_schema import skill

router = APIRouter()

@router.post("/resume-parse")
async def resume_parse(
     user_id:str,
     file: UploadFile = File(...),
     db:MongoDB = Depends(MongoDB)
):
     try:
          file_extension = file.filename.split(".")[-1]
          resume_text = await FileHandler.file_handler(file.read(), file_extension)
          result = await ResumeParseService().parse_resume(resume_text)
          await db.insert_resume_parse_info(user_id,result)
          return result
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))

@router.put("/upsert_skill")
async def upsert_skill(
     user_id:str,
     skill:skill,
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


