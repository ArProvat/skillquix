

from pydantic import BaseModel, Field

class UserSkillGapRequest(BaseModel):
     user_id: str = Field(..., description="User ID")
     gig_id: str = Field(..., description="Gig ID")

class UserSkillGapResponse(BaseModel):
     match_skills_of_user_with_gig: list[str] = Field(..., description="Match skills of user with gig at max 5 skills ")
     skill_gap_of_user_with_gig: list[str] = Field(..., description="Skill gap of user with gig at max 5 skills ")
     
     