from openai import AsyncOpenAI
from app.config.settings import settings
from .user_skillgap_schema import UserSkillGapResponse
from app.DB.mongodb.mongodb import MongoDB
from app.prompt.prompt import USER_SKILLGAP_USER_PROMPT , USER_SKILLGAP_SYSTEM_PROMPT


settings = settings()
mongodb = MongoDB()

class skillgap_service:
     def __init__(self):
          self.openai_client = AsyncOpenAI(
               api_key=settings.OPENAI_API_KEY
          )
          self.user_skillgap_system_prompt = settings.USER_SKILLGAP_SYSTEM_PROMPT
          self.user_skillgap_user_prompt = settings.USER_SKILLGAP_USER_PROMPT

          
          
          
     
     async def get_response(self, user_id: str, gig_id: str) -> UserSkillGapResponse:
          try:
               gig_description = await mongodb.get_gig_description(gig_id)
               user_resume = await mongodb.get_resume_by_user_id(user_id)

               prompt = self.user_skillgap_user_prompt.format(
                    gig_description=gig_description,
                    user_resume=user_resume
               )

               completion = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                         {"role": "system", "content": self.user_skillgap_system_prompt.format(output_format=UserSkillGapResponse.model_json_schema())},
                         {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
               )
               response = completion.choices[0].message.content

               if not response:
                    raise HTTPException(status_code=500, detail="No response from OpenAI")
               if response.startswith("```json"):
                    response = response[7:-3]
               
               return response               

          except Exception as e:
               raise HTTPException(status_code=500, detail=str(e))

          
          