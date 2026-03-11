from openai import AsyncOpenAI
from app.config.settings import settings
from app.prompt.prompt import resume_parse_system_prompt
from .resume_parse_schema import SkillQuixResume

class ResumeParseService:
     def __init__(self):
          self.client        = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
          self.system_prompt = resume_parse_system_prompt

     async def parse_resume(self, resume_text: str) -> SkillQuixResume:
          if not resume_text:
               raise ValueError("Resume text is required")

          try:
               completion = await self.client.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    messages=[
                         {
                         "role": "system",
                         "content": self.system_prompt.format(
                              schema=SkillQuixResume.model_json_schema()
                         )
                         },
                         {
                         "role": "user",
                         "content": resume_text
                         }
                    ],
                    temperature=0.5,
                    response_format=SkillQuixResume,   # ← returns parsed Pydantic object directly
               )

               result = completion.choices[0].message.parsed  # ← already SkillQuixResume
               
               if result is None:
                    raise ValueError("AI returned empty response")

               return result   # ← return directly, no string stripping needed

          except Exception as e:
               raise ValueError(f"Error parsing resume: {str(e)}")