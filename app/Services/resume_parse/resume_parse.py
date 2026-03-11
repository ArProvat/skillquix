from openai import AsyncOpenAI
from app.config.settings import settings
from app.prompt.prompt import resume_parse_system_prompt
from .resume_parse_schema import SkillQuixResume

class ResumeParseService:
     def __init__(self):
          self.client        = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
          self.system_prompt = resume_parse_system_prompt

     async def parse_resume(self, resume_text: str) -> SkillQuixResume:
          try:
               if not resume_text:
                    raise ValueError("Resume text is required")

               messages = [
                    {
                         "role": "system",
                         "content": self.system_prompt.format(schema=SkillQuixResume.model_json_schema())
                    },
                    {
                         "role": "user",
                         "content": resume_text
                    }
               ]

               completion = await self.client.chat.completions.create(
                    model="gpt-4o-mini",  
                    messages=messages,
                    temperature=0.5,
                    response_format={"type": "json_object"}
               )

               result = completion.choices[0].message.content
               if result.startswith("```json"):
                    result = result[7:-3]
               if result.startswith("```"):
                    result = result[3:-3]
               result = json.loads(result)
               
               return result

          except Exception as e:
               raise ValueError(f"Error parsing resume: {str(e)}")