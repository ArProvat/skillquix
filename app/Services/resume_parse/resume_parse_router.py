

from fastapi import APIRouter,HTTPException
from app.Services.resume_parse.resume_parse import ResumeParseService
from fastapi import UploadFile, File
from app.utils.file_handler import FileHandler


router = APIRouter()

@router.post("/resume-parse")
async def resume_parse(
     file: UploadFile = File(...),
):
     try:
          file_extension = file.filename.split(".")[-1]
          resume_text = await FileHandler.file_handler(file.read(), file_extension)
          result = await ResumeParseService().parse_resume(resume_text)
          return result
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
