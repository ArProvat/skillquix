from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from bson import ObjectId
from app.Services.resume_parse.resume_parse_schema import skill

class MongoDB:
     def __init__(self):
          self.client = AsyncIOMotorClient(settings.MONGODB_URL)
          self.db = self.client[settings.DB_NAME]
          self.user_collection = self.db['users']
          self.resume_collection = self.db['resumes']
          self.cover_letter_collection = self.db['cover_letters']
          self.job_collection = self.db['jobs']
          

     def get_db(self):
          return self.db
     async def initial_index(self):
          await self.user_collection.create_index([('email', 1)], unique=True)
          await self.resume_collection.create_index([('user_id', 1)])
          await self.cover_letter_collection.create_index([('user_id', 1)])
          await self.job_collection.create_index([('user_id', 1)])

     async def insert_resume_parse_info(self,user_id:str,user_resume:dict):
          try:
               user_id = ObjectId(user_id)
               user_resume['user_id'] = user_id
               
               # comment: insert user resume
               result = await self.resume_collection.insert_one(user_resume)
               return {"message":"Resume parsed successfully","resume_id":str(result.inserted_id)}
               
          except Exception as e:
               raise e
          # end try
     async def get_resume_by_user_id(self,user_id:str):
          try:
               user_id = ObjectId(user_id)
               resume = await self.resume_collection.find_one({'user_id':user_id})
               if resume:
                    resume['_id'] = str(resume['_id'])
                    resume['user_id'] = str(resume['user_id'])
               return resume
          except Exception as e:
               raise e
          # end try
     
     async def update_resume_parse_info(self,user_id:str,user_resume:dict):
          try:
               user_id = ObjectId(user_id)
               
               # comment: update user resume
               result = await self.resume_collection.update_one({'user_id':user_id},{"$set":user_resume})
               return {"message":"Resume parsed successfully","resume_id":str(result.upserted_id)}
               
          except Exception as e:
               raise e
          # end try

     from bson import ObjectId

     async def smart_upsert_skill(self, user_id: str, skill:skill):
          try:
               oid = ObjectId(user_id)
               skill_name = skill.skills.name
               category = skill.category
               
               update_result = await self.resume_collection.update_one(
                    {
                         "_id": oid,
                         "tech_stack": {
                              "$elemMatch": {
                              "category": category,
                              "skills.skill": skill_name
                              }
                         }
                    },
                    {
                         "$set": {
                              "tech_stack.$[cat].skills.$[sk].proficiency_level": skill.skills.proficiency_level,
                              "tech_stack.$[cat].skills.$[sk].years_of_experience": skill.skills.years_of_experience
                         }
                    },
                    array_filters=[
                         {"cat.category": category},
                         {"sk.skill": skill_name}
                    ]
               )

               # 2. If no skill was updated, it means either the skill or category is missing
               if update_result.matched_count == 0:
                    # Reuse your insert logic: push to category if exists, or create new category
                    await self.resume_collection.bulk_write([
                         # Push to existing category
                         UpdateOne(
                              filter={'_id': oid, "tech_stack.category": category},
                              update={"$push": {"tech_stack.$.skills": skill.skills}}
                         ),
                         # Create category if missing
                         UpdateOne(
                              filter={'_id': oid, "tech_stack.category": {"$ne": category}},
                              update={
                              "$push": {
                                   "tech_stack": {"category": category, "skills": [skill.skills]}
                              }
                              }
                         )
                    ])
                    return {"message": "New skill/category added successfully"}
               
               return {"message": "Existing skill info updated"}

          except Exception as e:
               print(f"Smart Upsert Error: {e}")
               raise e

     async def get_skill(self,user_id:str):
          try:
               user_id = ObjectId(user_id)
               skill = await self.resume_collection.find_one({'user_id':user_id},{"tech_stack":1})
               
               return skill
          except Exception as e:
               raise e
          # end try

     async def insert_cover_letter_info(self,user_id:str,cover_letter:dict):
          try:
               user_id = ObjectId(user_id)
               cover_letter['user_id'] = user_id
               
               # comment: insert user cover letter
               result = await self.cover_letter_collection.insert_one(cover_letter)
               return {"message":"Cover letter inserted successfully","cover_letter_id":str(result.inserted_id)}
               
          except Exception as e:
               raise e
          # end try

     async def get_cover_letter_by_user_id(self,user_id:str):
          try:
               user_id = ObjectId(user_id)
               cover_letter = await self.cover_letter_collection.find_one({'user_id':user_id})
               if cover_letter:
                    cover_letter['_id'] = str(cover_letter['_id'])
                    cover_letter['user_id'] = str(cover_letter['user_id'])
               return cover_letter
          except Exception as e:
               raise e
          # end try
     