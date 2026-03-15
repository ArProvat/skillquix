from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from bson import ObjectId

class MongoDB:
     def __init__(self):
          self.client = AsyncIOMotorClient(settings.MONGODB_URL)
          self.db = self.client[settings.DB_NAME]
          self.user_collection = self.db['User']
          self.resume_collection = self.db['ResumeProfile']
          self.cover_letter_collection = self.db['CoverLetter']
          self.job_collection = self.db['Gig']
          self.recommended_skill_collection = self.db['Matches']
          self.skill_impact_collection = self.db['SkillImpact']
          self.matches_collection = self.db['Matches']
          self.clearityScore_collection = self.db['ClearityScore']
          self.activityLog_collection = self.db['ActivityLog']
          self.skillGap_collection = self.db['SkillGap']


     def get_db(self):
          return self.db

     async def initial_index(self):
          await self.user_collection.create_index([('email', 1)], unique=True)
          await self.resume_collection.create_index([('user_id', 1)])
          await self.cover_letter_collection.create_index([('user_id', 1)])
          await self.job_collection.create_index([('user_id', 1)])
          await self.recommended_skill_collection.create_index([('user_id', 1)])
          await self.skill_impact_collection.create_index([('skill', 1)])
          await self.matches_collection.create_index([('user_id', 1)])
          await self.clearityScore_collection.create_index([('user_id', 1)])
          await self.activityLog_collection.create_index([('user_id', 1),('createdAt', 1)])


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
     
     async def insert_recommended_skill(self,user_id:str,recommended_skill:dict):
          try:
               user_id = ObjectId(user_id)
               exist= await self.recommended_skill_collection.find_one({'user_id':user_id})
               if exist:
                    await self.recommended_skill_collection.update_one({'user_id':user_id},{"$push":{"recommended_skills":recommended_skill.recommended_skills}})
                    return {"message":"Recommended skill updated successfully","recommended_skill_id":str(exist['_id'])}  
               # comment: insert user recommended skill
               recommended_skill['user_id'] = user_id
               result = await self.recommended_skill_collection.insert_one(recommended_skill)
               return {"message":"Recommended skill inserted successfully","recommended_skill_id":str(result.inserted_id)}
               
          except Exception as e:
               raise e
          # end try

     async def get_recommended_skill(self,user_id:str):
          try:
               user_id = ObjectId(user_id)
               recommended_skill = await self.recommended_skill_collection.find_one({'user_id':user_id})
               if recommended_skill:
                    recommended_skill['_id'] = str(recommended_skill['_id'])
                    recommended_skill['user_id'] = str(recommended_skill['user_id'])
               return recommended_skill
          except Exception as e:
               raise e
          # end try
     
     async def insert_skill_impact(self,skill:str,skill_impact:dict):
          try:
               
               skill_impact['skill'] = skill
               
               result = await self.skill_impact_collection.insert_one(skill_impact)
               return {"message":"Skill impact inserted successfully","skill_impact_id":str(result.inserted_id)}
               
          except Exception as e:
               raise e
          
     async def get_skill_impact(self,skill:str):
          try:
               skill_impact = await self.skill_impact_collection.find_one({'skill':skill},{
                    "_id":0,
                    "skill":0,
               })
               return skill_impact
          except Exception as e:
               raise e

     async def get_user_resume(self, user_id: str):
          try:
               user_id = ObjectId(user_id)
               resume = await self.resume_collection.find_one({'user_id':user_id},{
                    "_id":0,
                    "user_id":0,
                    "createdAt":0,
                    "updatedAt":0,
                    
               })
               
               return resume
          except Exception as e:
               raise e
     async def get_user_skill(self,user_id:str):
          try:
               user_id = ObjectId(user_id)
               skill = await self.resume_collection.find_one({'user_id':user_id},{
                    "tech_stack":1,
                    "_id":0,
                    "user_id":0,
                    "createdAt":0,
                    "updatedAt":0,
                    
               })
               return skill
          except Exception as e:
               raise e
     async def get_gig_description(self, gig_id: str):
          try:
               gig_id = ObjectId(gig_id)
               gig = await self.job_collection.find_one({'_id':gig_id},{
                    "responsibilities":1,
                    "jobDescription":1,
                    "_id":0,
                    "user_id":0,
                    "createdAt":0,
                    "updatedAt":0,
                    
               })
               return "Responsibilities: " + " ".join(gig['responsibilities']) +"\n"+ "Job Description: " + " ".join(gig['jobDescription'])
          except Exception as e:
               raise e

     async def insert_skill_gap(self,user_id:str,gig_id:str,skill_gap:dict):
          try:
               user_id = ObjectId(user_id)
               gig_id = ObjectId(gig_id)
               skill_gap['user_id'] = user_id
               skill_gap['gig_id'] = gig_id
               result = await self.skillGap_collection.insert_one(skill_gap)
               return {"message":"Skill gap inserted successfully","skill_gap_id":str(result.inserted_id)}
          except Exception as e:
               raise e
     async def get_skill_gap(self,user_id:str,gig_id:str):
          try:
               user_id = ObjectId(user_id)
               gig_id = ObjectId(gig_id)
               skill_gap = await self.skillGap_collection.find_one({'user_id':user_id,'gig_id':gig_id},{
                    "_id":0,
                    "user_id":0,
                    "gig_id":0,
                    "createdAt":0,
                    "updatedAt":0,
                    
               })
               return skill_gap
          except Exception as e:
               raise e
