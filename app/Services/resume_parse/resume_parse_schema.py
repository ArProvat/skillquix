from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field, ConfigDict

# --- 1. Define specific shapes for dynamic data ---
class SkillData(BaseModel):
    model_config = ConfigDict(extra='forbid')
    category: str = Field(...,description="category of the skill")
    Skills: List[str] = Field(...,description="skills of the person")


class social_links(BaseModel):
     social_media: Optional[str] = Field(None,description="social media of the person")
     link: Optional[str] = Field(None,description="link of the social media")
# --- New: Specific shape for Certifications ---
class CertificationData(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(...,description="name of the certification")
    issuer: str = Field(...,description="issuer of the certification")
    issue_date: Optional[str] = Field(None, alias="issueDate",description="issue date of the certification")
    expiry_date: Optional[str] = Field(None, alias="expiryDate",description="expiry date of the certification")
    credential_id: Optional[str] = Field(None, alias="credentialId",description="credential id of the certification")
class ExperienceData(BaseModel):
    model_config = ConfigDict(extra='forbid')
    company: str = Field(...,description="company of the person")
    role: str = Field(...,description="role of the person")
    location: Optional[str] = Field(None,description="location of the person")
    start_date: Optional[str] = Field(None, alias="startDate",description="start date of the person")   # YYYY-MM-DD
    end_date: Optional[str] = Field(None, alias="endDate",description="end date of the person")       # null if current
    is_current: bool = Field(False, alias="isCurrent",description="is current of the person")
    duration: Optional[str] = None  # keep as fallback if dates unparseable
    responsibilities: List[str]
    tech_stack: List[str] = Field(default_factory=list, alias="techStack")
    achievements: List[str] = Field(default_factory=list)

class EducationData(BaseModel):
    model_config = ConfigDict(extra='forbid')
    institution: Optional[str] = Field(None,description="institution of the person")
    degree: Optional[str] = Field(None,description="degree of the person")
    field_of_study: Optional[str] = Field(None, alias="fieldOfStudy",description="field of study of the person")
    graduation_year: Optional[str] = Field(None, alias="graduationYear",description="graduation year of the person or expected graduation year or running")
    location: Optional[str] = Field(None,description="location of the institution if there")

class ProjectData(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: str = Field(...,description="title of the project")
    description: str = Field(...,description="description of the project")
    technologies: List[str] = Field(...,description="technologies used in the project")
    link: Optional[str] = Field(None,description="link to the project")

class GenericData(BaseModel):
    model_config = ConfigDict(extra='forbid')
    label: str = Field(...,description="label of the generic data")
    value: List[str] = Field(...,description="value of the generic data")
    description: Optional[str] = Field(None,description="description of the generic data")
# --- 2. The Dynamic Section Wrapper ---

from enum import Enum
class TableCell(BaseModel):
    model_config = ConfigDict(extra='forbid')
    value: str = Field(...,description="value of the table cell")
    column_header: Optional[str] = Field(None, alias="columnHeader",description="column header of the table cell")

class TableRow(BaseModel):
    model_config = ConfigDict(extra='forbid')
    row_index: int = Field(alias="rowIndex",description="row index of the table row")
    cells: List[TableCell] = Field(...,description="cells of the table row")

class TableData(BaseModel):
    model_config = ConfigDict(extra='forbid')
    headers: List[str] = Field(...,description="headers of the table")
    rows: List[TableRow] = Field(...,description="rows of the table")
    inferred_type: Optional[str] = Field(
        None,
        alias="inferredType",
        description="What the table represents e.g. skills_matrix, employment_history, certifications"
    )
    # If the AI can flatten the table into a known type, it does so here
    flattened_data: Optional[
        Union[SkillData, ExperienceData, CertificationData,social_links, GenericData]
    ] = Field(
        None,
        alias="flattenedData",
        description="If table maps cleanly to a known schema type, populate this"
    )
class FormatQuality(str, Enum):
    CLEAN = "clean"         # Source was well-structured
    NORMALIZED = "normalized"  # AI had to reformat
    INFERRED = "inferred"   # AI had to guess structure from context

class CandidateSectionItem(BaseModel):
    model_config = ConfigDict(extra='forbid')
    data: Union[ExperienceData, EducationData, ProjectData, CertificationData, GenericData,TableData]
    order_index: int = Field(default=0, alias="orderIndex")
    
    # --- NEW: Quality & Audit Fields ---
    format_quality: Optional[FormatQuality] = Field(
        None,
        alias="formatQuality",
        description="Indicates whether the AI had to reformat this item"
    )
    normalization_notes: Optional[str] = Field(
        None,
        alias="normalizationNotes", 
        description="Brief note on what was corrected e.g. 'merged fragmented bullet points in one line max 10 words'"
    )

class CandidateSection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    section_type: Literal["experience", "education", "projects", "research"] = Field(alias="sectionType")
    title: str
    order_index: int = Field(default=0, alias="orderIndex")
    items: List[CandidateSectionItem]

# --- 3. The Root Model ---

class Candidate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    domain: str= Field(...,description="domain of the resume")
    subdomain: str = Field(...,description="subdomain of the resume")
    name: str= Field(...,description="name of the person")
    email: str= Field(...,description="email of the person")
    phone: Optional[str] = Field(None,description="phone of the person")
    location: Optional[str] = Field(None,description="location of the person")
    summary: Optional[str] = Field(None,description="summary of the person")
    total_exp: Optional[str] = Field(None, alias="totalExp",description="total experience of the person")
    skills: List[SkillData] = Field(...,description="all categories of skills ")
    sections: List[CandidateSection] = Field(...,description="all sections of the resume")