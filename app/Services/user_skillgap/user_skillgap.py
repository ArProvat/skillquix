

from openai import AsyncOpenAI
from app.config.settings import settings
from .user_skillgap_schema import UserSkillGapResponse


settings = settings()

class skillgap_service:
     def __init__(self):
          self.openai_client = AsyncOpenAI(
               api_key=settings.OPENAI_API_KEY
          )
          self.user_skillgap_prompt = settings.USER_SKILLGAP_PROMPT

     async def get_user_resume(self, user_id: str) -> str:
          
          
     async def get_gig_description(self, gig_id: str) -> str:
          
     
     async def get_response(self, user_id: str, gig_id: str) -> UserSkillGapResponse:

          
          