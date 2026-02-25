from pydantic import BaseModel, Field
from typing import List

class SkillImpactSchema(BaseModel):
     impact_summary: str = Field(..., description="Impact summary")
     who_serve_this_skill: List[str] = Field(..., description="Who serve this skill")
     why_this_skill_is_important: str = Field(..., description="Why this skill is important")
     transferability: str = Field(..., description="Transferability")
     real_world_example: str = Field(..., description="Real world example")