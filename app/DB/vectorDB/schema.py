from pydantic import BaseModel
from typing import List

class UpsertEmbeddingRequest(BaseModel):
     embedding: List[float]

class UpsertResumeRequest(BaseModel):
     embedding: List[float]