

from openai import AsyncOpenAI
from app.config.settings import settings
from app.prompt.prompt import resume_parse_system_prompt
from .resume_parse_schema import UniversalResume


class ResumeParseService:
     def __init__(self):
          self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
          self.system_prompt = resume_parse_system_prompt

     async def parse_resume(self, resume_text: str) -> UniversalResume:
          try:
               print(resume_text)
               if not resume_text:
                    raise ValueError("Resume text is required")

               messages = [
                    {
                         "role": "system",
                         "content": self.system_prompt.format(schema=UniversalResume.model_json_schema())
                    },
                    {
                         "role": "user",
                         "content": resume_text
                    }
               ]

               completion = await self.client.beta.chat.completions.parse(
                    model="gpt-4o-mini",  
                    messages=messages,
                    temperature=0.5,
                    response_format=UniversalResume
               )

               return completion.choices[0].message.parsed

          except Exception as e:
               raise ValueError(f"Error parsing resume: {str(e)}")
