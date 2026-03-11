# resume_parse_schema.py
from __future__ import annotations
from typing import List, Optional, Union
from pydantic import BaseModel, Field


class ExperienceData(BaseModel):
     company:        str
     role:           str
     location:       Optional[str] = None
     duration:       Optional[str] = None
     employmentType: Optional[str] = None
     description:    Optional[str] = None
     techStack:      List[str] = Field(default_factory=list)


class ProjectData(BaseModel):
     name:        str
     role:        Optional[str] = None
     duration:    Optional[str] = None
     techStack:   List[str] = Field(default_factory=list)
     description: Optional[str] = None
     githubUrl:   Optional[str] = None   # ← str not HttpUrl
     liveUrl:     Optional[str] = None   # ← str not HttpUrl


class EducationData(BaseModel):
     institution: str
     degree:      Optional[str] = None
     field:       Optional[str] = None
     duration:    Optional[str] = None
     grade:       Optional[str] = None


class SkillData(BaseModel):
     category: str
     skills:   List[str] = Field(default_factory=list)


class CertificationData(BaseModel):
     name:          str
     issuedBy:      str
     issueDate:     Optional[str] = None
     expiryDate:    Optional[str] = None
     credentialUrl: Optional[str] = None  # ← str not HttpUrl


class SectionItem(BaseModel):
     id:         str
     orderIndex: int
     data:       dict = Field(default_factory=dict)  # ← plain dict, not Union


class ResumeSection(BaseModel):
     id:          str
     sectionType: str
     title:       str
     orderIndex:  int
     items:       List[SectionItem] = Field(default_factory=list)


class Metadata(BaseModel):
     domain:    str = "general"
     subdomain: str = "general"


class SkillQuixResume(BaseModel):
     id:        str = ""
     name:      str = ""
     email:     str = ""
     phone:     Optional[str] = None
     location:  Optional[str] = None
     summary:   Optional[str] = None
     totalExp:  Optional[str] = None
     avatarUrl: Optional[str] = None
     sections:  List[ResumeSection] = Field(default_factory=list)
     metaData:  Metadata = Field(default_factory=Metadata)