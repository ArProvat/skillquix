from pydantic import BaseModel, Field
from typing import List, Optional

class Experience(BaseModel):
     company_name: str = Field(..., example="Company Name")
     position: str = Field(..., example="Position")
     start_date: str = Field(..., example="Start Date")
     end_date: str = Field(..., example="End Date")
     description: str = Field(..., example="Description")

class Education(BaseModel):
     school_name: str = Field(..., example="School Name")
     degree: str = Field(..., example="Degree")
     field_of_study: str = Field(..., example="Field of Study")
     result: str = Field(..., example="GPA / CGPA etc.")
     start_date: str = Field(..., example="Start Date")
     end_date: str = Field(..., example="End Date")
     description: str = Field(..., example="Description")

class Certificate(BaseModel):
     name: str = Field(..., example="Certificate name")
     issue_date: str = Field(..., example="Issue Date")

class Project(BaseModel):
     name: str = Field(..., example="Project name")
     link: str = Field(..., example="Project link")
     tech_stack: List[str] = Field(..., example=["Python", "FastAPI"])
     description: List[str] = Field(..., example=["Description line 1"])
     start_date: str = Field(..., example="Start Date")
     end_date: str = Field(..., example="End Date")

class SkillDetails(BaseModel):
     name: str = Field(..., example="Python")
     proficiency_level: str = Field(..., example="Advanced")
     years_of_experience: int = Field(..., example=3)

class Skill(BaseModel):
     category: str = Field(..., example="Backend")
     skills: List[SkillDetails] = Field(..., example=[])

class OtherLink(BaseModel):
     type: str = Field(..., example="LinkedIn")
     link: str = Field(..., example="https://linkedin.com/in/...")

class ResumeParse(BaseModel):
     name: str = Field(..., example="Candidate name")
     address: str = Field(..., example="Dhaka, Bangladesh")
     email: str = Field(..., example="email@example.com")
     phone: List[str] = Field(..., example=["+8801712345678"])
     professional_summary: Optional[str] = Field(None, example="Summary")   # None default, not ...
     tech_stack: Optional[List[Skill]] = Field(None, example=[])
     projects: Optional[List[Project]] = Field(None, example=[])
     work_experience: Optional[List[Experience]] = Field(None, example=[])
     education: Optional[List[Education]] = Field(None, example=[])
     other_links: Optional[List[OtherLink]] = Field(None, example=[])
     certificates: Optional[List[Certificate]] = Field(None, example=[])
     languages: Optional[List[str]] = Field(None, example=["Bengali", "English"])