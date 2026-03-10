from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
class ContactInfo(BaseModel):
     name: Optional[str] = Field(None, description="Full name of the candidate")
     email: Optional[str] = Field(None, description="Primary email address")
     phone: Optional[str] = Field(None, description="Contact phone number with country code")
     location: Optional[str] = Field(None, description="City, State, and Country")
     links: List[Dict[str, str]] = Field(
          default_factory=list, 
          description="Social links like LinkedIn, GitHub, Portfolio, or ResearchGate"
     )

class WorkExperience(BaseModel):
     company: str = Field(..., description="Name of the organization")
     title: str = Field(..., description="Job title or role")
     start_date: Optional[str] = Field(None, description="Start date (ISO format preferred)")
     end_date: Optional[str] = Field(None, description="End date or 'Present'")
     description: List[str] = Field(
          default_factory=list, 
          description="Bullet points of responsibilities and achievements"
     )
     is_current: bool = Field(False, description="Whether the candidate currently works here")

class Education(BaseModel):
     institution: str = Field(..., description="University or school name")
     degree: Optional[str] = Field(None, description="Degree type (e.g., BS, PhD, MD)")
     major: Optional[str] = Field(None, description="Field of study")
     graduation_date: Optional[str] = Field(None, description="Date of completion")

class Skill(BaseModel):
     name: str = Field(..., description="The specific skill name (e.g., Python, Suturing, SEO)")
     category: Optional[str] = Field(None, description="Category (e.g., Programming, Medical, Language)")
     level: Optional[str] = Field(None, description="Proficiency level (e.g., Expert, Intermediate)")

class DynamicSection(BaseModel):
     section_title: str = Field(..., description="The header found in the resume (e.g., 'Publications', 'Clinical Rotations')")
     content: List[Dict[str, Any]] = Field(
          ..., 
          description="The extracted details of this section in a structured key-value format"
     )
class UnstructuredAdditionalData(BaseModel):
     title: str = Field(..., description="The topic or category of the data")
     value: list[Any] = Field(..., description="The data itself")

class dynamic_meta_info(BaseModel):
     title: str = Field(..., description="The title of the meta info")
     value: list[Any] = Field(..., description="The value of the meta info")
class metainfo(BaseModel):
     detected_domain: Optional[str] = Field(None, description="The industry detected from the resume")
     detected_sub_domain: Optional[str] = Field(None, description="The sub domain detected from the resume")
     years_of_experience: Optional[str] = Field(None, description="The years of experience extracted from the resume")
     tone_analysis: Optional[str] = Field(None, description="The tone analysis of the resume")
     Language:Optional[List[str]] = Field(None, description="The language detected from the resume")
     dynamic_meta_info: Optional[List[dynamic_meta_info]] = Field(None, description="The dynamic meta info of the resume")
class UniversalResume(BaseModel):
     # --- STATIC CORE ---
     basics: ContactInfo = Field(..., description="Essential contact information")

     summary: Optional[str] = Field(None, description="Professional profile or executive summary")
     
     # --- STATIC BUT MANDATORY ---
     skills: List[Skill] = Field(
          ..., 
          description="A list of technical, soft, or industry-specific skills extracted from the resume"
     )
     
     experience: List[WorkExperience] = Field(default_factory=list)
     education: List[Education] = Field(default_factory=list)

     # --- THE DYNAMIC OVERFLOW ---
     industry_specific_sections: List[DynamicSection] = Field(
          default_factory=list,
          description="Captures industry-specific data like Research Papers, Medical Board Certifications, or Design Awards."
     )

     unstructured_additional_data: List[UnstructuredAdditionalData] = Field(
          default_factory=list,
          description="A catch-all field for any information that does not fit into standard sections. Key is the topic, Value is the data."
     )

     metadata: Dict[metainfo] = Field(
          default_factory=dict,
          description="System-level info like 'industry_detected', 'years_of_experience', or 'tone_analysis'"
     )