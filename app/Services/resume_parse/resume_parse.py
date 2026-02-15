

from openai import AsyncOpenAI
from app.config.settings import settings
from app.prompt.prompt import resume_parse_system_prompt
from resume_parse_schema import ResumeParse



class ResumeParseService:
     def __init__(self):
          self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
          self.system_prompt = resume_parse_system_prompt

     async def parse_resume(self, resume_text: str) -> ResumeParse:
          try:
               if not resume_text:
                    raise ValueError("Resume text is required")

               messages = [
                    {
                         "role": "system",
                         "content": self.system_prompt.format(schema=ResumeParse.model_json_schema())
                    },
                    {
                         "role": "user",
                         "content": resume_text
                    }
               ]

               completion = await self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=2000,
                    temperature=0.5,
                    response_format=ResumeParse
               )

               response = completion.choices[0].message.content
               if response.startswith("```json"):
                    response = response[7:-3]
               return ResumeParse(**response)
          except Exception as e:
               raise ValueError(f"Error parsing resume: {str(e)}")
               


