from __future__ import annotations
from typing import List, Optional, Union, Literal, Any
from pydantic import BaseModel, Field, HttpUrl

# --- 1. Define Data Models for different section types ---

class ExperienceData(BaseModel):
     company: str
     role: str
     location: Optional[str] = None
     duration: Optional[str] = None
     employmentType: Optional[str] = None
     description: Optional[str] = None
     techStack: List[str] = Field(default_factory=list)

class ProjectData(BaseModel):
     name: str
     role: Optional[str] = None
     duration: Optional[str] = None
     techStack: List[str] = Field(default_factory=list)
     description: Optional[str] = None
     githubUrl: Optional[str] = None
     liveUrl: Optional[str] = None

class EducationData(BaseModel):
     institution: str
     degree: Optional[str] = None
     field: Optional[str] = None
     duration: Optional[str] = None
     grade: Optional[str] = None

class SkillData(BaseModel):
     category: str
     skills: List[str] = Field(default_factory=list)

class CertificationData(BaseModel):
     name: str
     issuedBy: str
     issueDate: Optional[str] = None
     expiryDate: Optional[str] = None
     credentialUrl: Optional[str] = None

# --- 2. Define the Item Wrappers ---

class SectionItem(BaseModel):
     id: str
     orderIndex: int
     # Using 'Any' or a Union here depends on how strict you want to be
     data: Union[ExperienceData, ProjectData, EducationData, SkillData, CertificationData, dict]

# --- 3. Define the Section Wrapper ---

class ResumeSection(BaseModel):
     id: str
     sectionType: str # e.g., "experience", "education", "skills"
     title: str
     orderIndex: int
     items: List[SectionItem]

# --- 4. Main Resume Model ---

class Metadata(BaseModel):
     domain:    str = ""    # ← default empty string
     subdomain: str = ""    # ← default empty string

class SkillQuixResume(BaseModel):
     id: str
     name: str
     email: str
     phone: Optional[str] = None
     location: Optional[str] = None
     summary: Optional[str] = None
     totalExp: Optional[str] = None
     avatarUrl: Optional[str] = None 
     sections: List[ResumeSection] = Field(default_factory=list)
     metaData: Metadata = Field(default_factory=Metadata)
