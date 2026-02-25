from openai import AsyncOpenAI
from .refelection_schema import refelectionResponse
from app.prompt.prompt import refelection_system_prompt, refelection_user_prompt
from app.config.settings import settings


class refelection:
     def __init__(self):
          self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

     async def ger_response(self, work_text: str, reasoning_text: str, impact_text: str) -> refelectionResponse:
          completion = await self.client.beta.chat.completions.parse(
               model="gpt-4o-mini",
               messages=[
                    {
                         "role": "system",
                         "content": refelection_system_prompt.format(
                         output_schema=refelectionResponse.model_json_schema()
                         )
                    },
                    {
                         "role": "user",
                         "content": refelection_user_prompt.format(
                         work_text=work_text,
                         reasoning_text=reasoning_text,
                         impact_text=impact_text
                         )
                    },
               ],
               response_format=refelectionResponse,  
          )

          return completion.choices[0].message.parsed  
