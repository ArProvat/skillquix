from openai import AsyncOpenAI
from .refelection_schema import refelectionResponse
from app.prompt.prompt import refelection_system_prompt, refelection_user_prompt



class refelection:
     def __init__(self):
          self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

     async def refelection(self, work_text: str, reasoning_text: str, impact_text: str) -> refelectionResponse:
          try:
               completion = await self.client.chat.completions.create(
               model="gpt-4o-mini",
               messages=[
                    {"role": "system", "content": refelection_system_prompt.format(output_schema=refelectionResponse.model_json_schema())},
                    {"role": "user", "content": refelection_user_prompt.format(work_text=work_text, reasoning_text=reasoning_text, impact_text=impact_text)},
               ],
               response_format={"type": "json_object"},
          )
               response = completion.choices[0].message.content

               if response.startswith("```json"):
                    response = response[7:-3]
               

               return refelectionResponse(**response)
          except Exception as e:
               print(e)
               return refelectionResponse()
