from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from app.config.settings import settings
from app.prompt.prompt import recommend_skill_system_prompt, recommend_skill_user_prompt
from .recommend_skill_schema import RecommendedSkill
from app.DB.mongodb.mongodb import MongoDB
import json
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun




class RecommendSkillAgent:
     def __init__(self):
          self.model = ChatOpenAI(
               model="gpt-5",
               temperature=0.1,
               max_tokens=1000,
               timeout=30
          )
          self.system_prompt = recommend_skill_system_prompt.format(schema=RecommendedSkill.model_json_schema())
          self.tools = [self.search]
          self.user_prompt = recommend_skill_user_prompt
          self.db = MongoDB()

     @tool
     def search(self, query: str) -> str:
          search = DuckDuckGoSearchRun()
          return search.invoke(query)
     
     async def get_response(self, user_id: str):
          try:
               resume_text = await self.db.get_resume_by_user_id(user_id)
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
               agent = create_agent(self.model, tools=self.tools, system_prompt=self.system_prompt)

               output_content = agent.invoke({
                    "messages": [
                         {"role": "user", "content": self.user_prompt.format(user_resume=resume_text)}
                    ]
               })
               print(output_content)
               if output_content.startswith("```json"):
                    output_content = output_content[7:-3]
               elif output_content.startswith("```"):
                    output_content = output_content[3:-3]

               parsed_result = json.loads(output_content)

               recommended_skills = RecommendedSkill(**parsed_result)

               skill_dict = recommended_skills.model_dump()
               await self.db.insert_recommended_skill(user_id, skill_dict)

               return recommended_skills

          except Exception as e:
               raise e
