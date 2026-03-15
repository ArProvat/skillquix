import json
from openai import AsyncOpenAI
from app.config.settings import settings
from app.prompt.prompt import resume_parse_system_prompt
from .resume_parse_schema import Candidate

class ResumeParseService:
     def __init__(self):
          self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
          self.system_prompt = resume_parse_system_prompt

     async def parse_resume(self, resume_text: str) -> Candidate:
          try:
               if not resume_text:
                    raise ValueError("Resume text is required")

               messages = [
                    {
                         "role": "system",
                         "content": self.system_prompt.format(schema=Candidate.model_json_schema())
                    },
                    {
                         "role": "user",
                         "content": resume_text
                    }
               ]

               # Using .beta.chat.completions.parse for Structured Outputs
               completion = await self.client.beta.chat.completions.parse(
                    model="gpt-4o-mini",  
                    messages=messages,
                    response_format=Candidate
               )

               result = completion.choices[0].message.parsed
               
               if not result:
                    raise ValueError("Model failed to parse the resume into the schema.")
                    
               return result

          except Exception as e:
               # This captures validation errors or API errors
               raise ValueError(f"Error parsing resume: {str(e)}")