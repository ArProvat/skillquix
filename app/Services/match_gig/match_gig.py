

import asyncio
from sentence_transformers import SentenceTransformer
import numpy as np
from fastapi import HTTPException
from app.DB.mongodb.mongodb import MongoDB
from app.DB.vectorDB.vectordb import search_similar_gigs
from bson import ObjectId

class MatchGig:
     def __init__(self):
          self.model = SentenceTransformer('all-MiniLM-L6-v2')
          self.mongodb = MongoDB()

     async def get_embedding(self, text: str):
          try:
               loop = asyncio.get_event_loop()
               embedding = await loop.run_in_executor(None, self.model.encode, text)  
          except Exception as e:
               raise HTTPException(status_code=500, detail=str(e))

     async def get_similar_gigs(self, user_id: str) -> list:
          # 1. Get resume embedding from MongoDB (backend already saved it)
          resume_doc = await self.mongodb.resume_collection.find_one({"userId": user_id})
          if not resume_doc:
               raise HTTPException(status_code=404, detail="Resume not found")

          embedding = resume_doc.get("embedding")
          if not embedding:
               raise HTTPException(status_code=400, detail="Resume has no embedding yet")

          # 2. Ask Qdrant for top 100 similar gig IDs
          gig_ids = await search_similar_gigs(embedding, limit=100)

          # 3. Fetch full gig docs from MongoDB in one query
          object_ids = [ObjectId(gid) for gid in gig_ids]
          cursor = self.mongodb.job_collection.find({"_id": {"$in": object_ids}})
          gigs = await cursor.to_list(length=100)

          # 4. Filter and return
          return self.filter_gigs(gigs)

     def filter_gigs(self, gigs: list) -> list:
          now = datetime.now(timezone.utc)
          filtered = []

          for gig in gigs:
               if gig.get("gigStatus") != "ACTIVE":
                    continue

               valid_until = gig.get("validUntil")
               if valid_until:
                    if valid_until.tzinfo is None:
                         valid_until = valid_until.replace(tzinfo=timezone.utc)
                    if valid_until < now:
                         continue



