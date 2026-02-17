

from pydantic import BaseModel, Field
from typing import List, Optional

class Skill(BaseModel):
     category: str = Field(..., example="Programming Languages")
     skill: str = Field(..., example="Python")
     demand_level: str = Field(..., example="High,Medium,Low")
     reason: str = Field(..., example="why this skill is recommended for the user in 2 line ")

class RecommendedSkill(BaseModel):
     recommended_skills: List[Skill]