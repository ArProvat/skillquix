from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_community.tools import DuckDuckGoSearchRun
from app.config.settings import settings
from app.prompt.prompt import recommend_skill_system_prompt, recommend_skill_user_prompt
from .recommend_skill_schema import RecommendedSkill
from app.DB.mongodb.mongodb import MongoDB


ddg_search = DuckDuckGoSearchRun()

@tool
def search(query: str) -> str:
     """Search the web for current in-demand skills and job market trends."""
     return ddg_search.invoke(query)


class RecommendSkillAgent:
     def __init__(self):
          self.model = ChatOpenAI(
               model="gpt-4o-mini",
               temperature=0.1,
               max_tokens=4000,  
               timeout=60
          )
          self.system_prompt = recommend_skill_system_prompt
          self.tools = [search]
          self.user_prompt = recommend_skill_user_prompt
          self.db = MongoDB()

     async def get_response(self, user_id: str) -> RecommendedSkill:
          # Fetch resume from DB
          resume_text = None #await self.db.get_resume_by_user_id(user_id)

          if not resume_text:
               resume_text = """
               Name: Md. Abdur Rahman
               Email: [EMAIL_ADDRESS]
               Phone: +8801712345678
               Address: Dhaka, Bangladesh
               Professional Summary: Experienced software engineer with 5+ years of experience in web development and mobile app development.
               Tech Stack: Python, Django, Flask, React, React Native, Node.js, Express.js, MongoDB, MySQL, Git, GitHub, Docker, AWS
               Projects: E-commerce website, Mobile banking app, Task management app
               Work Experience: Software Engineer at XYZ Company (2020-2022), Senior Software Engineer at ABC Company (2022-Present)
               Education: Bachelor of Science in Computer Science and Engineering from University of Dhaka (2016-2020)
               Other Links: LinkedIn, GitHub
               Certificates: AWS Certified Solutions Architect - Associate
               Languages: Bengali, English
               """

          # create_agent with response_format handles structured output — no JSON parsing needed
          agent = create_agent(
               model=self.model,
               #tools=self.tools,
               system_prompt=self.system_prompt,
               response_format=ToolStrategy(RecommendedSkill)
          )

          result = await agent.ainvoke({  # ainvoke for async — never block the event loop
               "messages": [
                    {
                         "role": "user",
                         "content": self.user_prompt.format(user_resume=resume_text)
                    }
               ]
          })

          recommended_skills: RecommendedSkill = result["structured_response"]

          # Persist to DB
          #await self.db.insert_recommended_skill(user_id, recommended_skills.model_dump())

          return recommended_skills
               