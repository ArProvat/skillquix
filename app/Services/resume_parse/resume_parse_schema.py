
from pydantic import BaseModel , Field
from typing import List, Optional

class experience(BaseModel):
     company_name: str = Field(..., example="Company Name")
     position: str = Field(..., example="Position")
     start_date: str = Field(..., example="Start Date")
     end_date: str = Field(..., example="End Date")
     description: str = Field(..., example="Description")

class education(BaseModel):
     school_name: str = Field(..., example="School Name")   
     degree: str = Field(..., example="Degree")
     field_of_study: str = Field(..., example="Field of Study")
     result: str = Field(..., example="Result of the education in GPA / CGPA etc.")
     start_date: str = Field(..., example="Start Date of the education")
     end_date: str = Field(..., example="End Date of the education")
     description: str = Field(..., example="Description of the education")
class certificate(BaseModel):
     name: str = Field(..., example="Name of the certificate")
     issue_date: str = Field(..., example="Issue Date of the certificate")

class project(BaseModel):
     name: str = Field(..., example="Name of the project") 
     link: str = Field(..., example="Link to the project")
     tech_stack: List[str] = Field(..., example="Tech Stack user to build the project")
     description: List[str] = Field(..., example="Description of the project")
     start_date: str = Field(..., example="Start Date")
     end_date: str = Field(..., example="End Date")

class skill(BaseModel):
     top_skills: List[str] = Field(..., example="Top Skills are most used in the resume and projects")
     soft_skills: List[str] = Field(..., example="Soft Skills are most used in the resume and projects")
     tools_and_platforms: List[str] = Field(..., example="Tools and Platforms are most used in the resume and projects")
     programming_languages: List[str] = Field(..., example="Programming Languages are most used in the resume and projects")

class other_links(BaseModel):
     type: str = Field(..., example="Type of the link like LinkedIn, GitHub etc.")
     link: str = Field(..., example="Link to the other link")
class ResumeParse(BaseModel):
     Name: str = Field(..., example="Name of the candidate")
     address: str = Field(..., example="Address of the candidate")
     Email: str = Field(..., example="Email of the candidate")
     Phone: List[str] = Field(..., example="Phone of the candidate")
     Skills: Optional[skill] = Field(..., example="Skills of the candidate")
     projects: Optional[List[project]] = Field(..., example="Projects of the candidate")
     work_experience: Optional[List[experience]] = Field(..., example="Work Experience of the candidate")
     Education: Optional[List[education]] = Field(..., example="Education of the candidate")
     other_links: Optional[List[other_links]] = Field(..., example="Other links of the candidate")
     certificates: Optional[List[certificate]] = Field(..., example="Certificates of the candidate")
     languages: Optional[List[str]] = Field(..., example="list of languages candidate know")