
from openai import AsyncOpenAI
from app.config.settings import settings
from app.prompt.prompt import skill_impact_system_prompt, skill_impact_user_prompt
from .skill_impact_schema import SkillImpactSchema
from app.DB.mongodb.mongodb import MongoDB





class SkillImpact:
     def __init__(self):
          self.llm = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
          self.mongodb = MongoDB()

     async def get_skill_impact(self,skill):
          try:
               skill = skill.lower()
               skill_impact = await self.mongodb.get_skill_impact(skill)
               if skill_impact:
                    return skill_impact

               response = await self.llm.chat.completions.create(
                    model="gpt-5-mini",
                    messages=[
                         {"role": "system", "content": skill_impact_system_prompt.format(schema=SkillImpactSchema.model_json_schema())},
                         {"role": "user", "content": skill_impact_user_prompt.format(skill=skill)}
                    ]
                    response_format={"type": "json_object"}
               )

               response = response.choices[0].message.content
               if response.startswith("```json"):
                    response = response[7:-3]
               if response.startswith("```"):
                    response = response[3:-3]
               await self.mongodb.insert_skill_impact(skill,response)
               return response
          except Exception as e:
               raise HTTPException(status_code=500, detail=str(e))