

import asyncio
from sentence_transformers import SentenceTransformer
import numpy as np
from fastapi import HTTPException

class MatchGig:
     def __init__(self):
          self.model = SentenceTransformer('all-MiniLM-L6-v2')

     async def get_embedding(self, text: str):
          try:
               loop = asyncio.get_event_loop()
               embedding = await loop.run_in_executor(None, self.model.encode, text)  # ✅ run sync in thread
               return embedding.tolist()  # ✅ convert to list (see bug #2)
          except Exception as e:
               raise HTTPException(status_code=500, detail=str(e))

     
          