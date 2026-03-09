from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List


class refelectionResponse(BaseModel):
     skills: List[str] = Field(default_factory=list )
     impact_bullets: List[str] = Field(default_factory=list)
     summary: str = Field(default="")

