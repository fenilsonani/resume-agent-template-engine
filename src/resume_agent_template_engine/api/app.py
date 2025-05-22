from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, validator
from typing import Dict, Any, Optional, List
import os
import json
# from resume_agent_template_engine.core.resume_template_editing import TemplateEditing # Not used directly in app.py for now
from resume_agent_template_engine.templates.template_manager import TemplateManager
from resume_agent_template_engine.core.docx_generator import generate_resume_docx # Import DOCX generator
import tempfile
import uvicorn
from enum import Enum
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import re
from datetime import datetime

app = FastAPI(
    title="Resume and Cover Letter Template Engine API",
    description="API for generating professional resumes and cover letters from JSON data using customizable templates",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Resume Agent Template Engine"}

class DocumentType(str, Enum):
    RESUME = "resume"
    COVER_LETTER = "cover_letter"

class OutputFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"

class PersonalInfo(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None

# Helper function for date validation logic (used by Pydantic validators)
def check_date_format(date_str: str) -> str:
    try:
        if len(date_str) == 7:  # YYYY-MM
            datetime.strptime(date_str, "%Y-%m")
        elif len(date_str) == 10:  # YYYY-MM-DD
            datetime.strptime(date_str, "%Y-%m-%d")
        else:
            raise ValueError("Date format must be YYYY-MM or YYYY-MM-DD")
        return date_str
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM or YYYY-MM-DD")

# The old `validate_date_format` and `validate_resume_data` functions 
# have been removed as their functionality is now covered by Pydantic models and validators.

class ExperienceItem(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    startDate: str
    endDate: str # Can also be "Present"
    details: Optional[List[str]] = None

    @validator('startDate')
    def validate_start_date(cls, value):
        return check_date_format(value)

    @validator('endDate')
    def validate_end_date(cls, value):
        if value == "Present":
            return value
        return check_date_format(value)

class EducationItem(BaseModel):
    degree: str
    institution: str
    location: Optional[str] = None
    date: Optional[str] = None # Could be a year, range, or specific date. For now, simple string.
    details: Optional[List[str]] = None

class ProjectItem(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: Optional[List[str]] = None
    url: Optional[str] = None

class PublicationItem(BaseModel):
    title: str
    publisher: Optional[str] = None
    date: Optional[str] = None # Similar to education date
    url: Optional[str] = None

class CertificationItem(BaseModel):
    name: str
    issuer: Optional[str] = None
    date: Optional[str] = None # Similar to education date
    url: Optional[str] = None


class ResumeData(BaseModel):
    personalInfo: PersonalInfo
    professional_summary: Optional[str] = None
    experience: Optional[List[ExperienceItem]] = None
    education: Optional[List[EducationItem]] = None
    projects: Optional[List[ProjectItem]] = None
    articles_and_publications: Optional[List[PublicationItem]] = None
    achievements: Optional[List[str]] = None
    certifications: Optional[List[CertificationItem]] = None
    technologies_and_skills: Optional[List[str]] = None
    # Add other fields as necessary based on common resume structures or future needs

class DocumentRequest(BaseModel):
    document_type: DocumentType
    template: str # Kept for PDF, might be ignored or used differently for DOCX if no "template" concept applies
    format: OutputFormat = OutputFormat.PDF # Use the OutputFormat Enum
    data: ResumeData 
    clean_up: bool = True

@app.post("/generate")
async def generate_document(request: DocumentRequest, background_tasks: BackgroundTasks):
    """
    Generate a resume or cover letter from the provided JSON data using the specified template.

    Args:
        request: DocumentRequest object containing document type, template choice, format, and data
        background_tasks: BackgroundTasks object to add cleanup tasks
        
    Returns:
        FileResponse containing the generated document
    """
    try:
        # Data validation is now handled by Pydantic models.
        # The call to validate_resume_data(request.data) is no longer needed.
        
        # Initialize template manager to validate templates
        template_manager = TemplateManager()
        available_templates = template_manager.get_available_templates()
        
        # Validate document type
        if request.document_type not in available_templates:
            raise HTTPException(
                status_code=404, 
                detail=f"Document type '{request.document_type}' not supported. Available types: {list(available_templates.keys())}"
            )
            
        # Validate template exists
        if request.template not in available_templates[request.document_type]:
            raise HTTPException(
                status_code=404, 
                detail=f"Template '{request.template}' not found for {request.document_type}. Available templates: {available_templates[request.document_type]}"
            )
        
        # Prepare common variables
        person_name = request.data.personalInfo.name.replace(' ', '_') if request.data.personalInfo and request.data.personalInfo.name else 'output'
        
        if request.format == OutputFormat.PDF:
            # Validate template for PDF generation
            if request.document_type not in available_templates:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Document type '{request.document_type}' not supported for PDF. Available types: {list(available_templates.keys())}"
                )
            if request.template not in available_templates[request.document_type]:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Template '{request.template}' not found for {request.document_type}. Available templates: {available_templates[request.document_type]}"
                )

            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                output_path = tmp_file.name
            
            try:
                template_instance = template_manager.create_template(
                    request.document_type, 
                    request.template, 
                    request.data.dict(exclude_unset=True)
                )
                template_instance.export_to_pdf(output_path)
                
                filename = f"{request.document_type.value}_{person_name}.pdf"
                media_type = 'application/pdf'
                
            except Exception as e: # Catch specific errors from PDF generation if possible
                if os.path.exists(output_path): # Cleanup temp file on error
                    os.remove(output_path)
                raise HTTPException(status_code=500, detail=f"PDF Generation Error: {str(e)}")

        elif request.format == OutputFormat.DOCX:
            if request.document_type == DocumentType.COVER_LETTER:
                 raise HTTPException(status_code=400, detail="DOCX format is currently only supported for resumes.")

            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
                output_path = tmp_file.name
            
            try:
                generate_resume_docx(
                    resume_data_dict=request.data.dict(exclude_unset=True), 
                    output_path=output_path
                )
                filename = f"resume_{person_name}.docx" # DOCX only for resume for now
                media_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

            except Exception as e: # Catch specific errors from DOCX generation
                if os.path.exists(output_path): # Cleanup temp file on error
                    os.remove(output_path)
                raise HTTPException(status_code=500, detail=f"DOCX Generation Error: {str(e)}")
        
        else:
            # This case should ideally not be reached if OutputFormat Enum is used correctly
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")

        # Common return logic for successful generation
        if request.clean_up:
            background_tasks.add_task(os.remove, output_path)
        
        return FileResponse(
            output_path,
            media_type=media_type,
            filename=filename
        )
            
    except ValueError as e: # Catches Pydantic validation errors and others
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/templates")
async def list_templates():
    """List all available templates by document type."""
    try:
        template_manager = TemplateManager()
        available_templates = template_manager.get_available_templates()
        return {"templates": available_templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/templates/{document_type}")
async def list_templates_by_type(document_type: DocumentType):
    """List all available templates for a specific document type."""
    try:
        template_manager = TemplateManager()
        available_templates = template_manager.get_available_templates(document_type)
        return {"templates": available_templates}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/template-info/{document_type}/{template_name}")
async def get_template_info(document_type: DocumentType, template_name: str):
    """Get detailed information about a specific template."""
    try:
        template_manager = TemplateManager()
        available_templates = template_manager.get_available_templates()
        
        if document_type not in available_templates:
            raise HTTPException(status_code=404, detail=f"Document type '{document_type}' not found")
        
        if template_name not in available_templates[document_type]:
            raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
        
        template_dir = os.path.join("templates", document_type, template_name)
        
        # Check for preview image
        preview_url = None
        for ext in ['.png', '.jpg', '.jpeg']:
            preview_path = os.path.join(template_dir, f"preview{ext}")
            if os.path.exists(preview_path):
                preview_url = f"/templates/{document_type}/{template_name}/preview{ext}"
                break
        
        return {
            "name": template_name,
            "document_type": document_type,
            "preview_url": preview_url,
            "description": f"{template_name.capitalize()} template for {document_type.replace('_', ' ')}",
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema/{document_type}")
async def get_document_schema(document_type: DocumentType):
    """Get the expected JSON schema for a specific document type."""
    try:
        if document_type == DocumentType.RESUME:
            return {
                "schema": {
                    "type": "object",
                    "required": ["personalInfo"],
                    "properties": {
                        "personalInfo": {
                            "type": "object",
                            "required": ["name", "email"],
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string"},
                                "phone": {"type": "string"},
                                "location": {"type": "string"},
                                "website": {"type": "string"},
                                "linkedin": {"type": "string"}
                            }
                        }
                    }
                },
                "example": {
                    "personalInfo": {
                        "name": "John Doe",
                        "email": "john@example.com"
                    }
                }
            }
        else:
            return {
                "schema": {
                    "type": "object",
                    "required": ["personalInfo", "content"],
                    "properties": {
                        "personalInfo": {
                            "type": "object",
                            "required": ["name", "email"],
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string"}
                            }
                        },
                        "content": {"type": "string"}
                    }
                },
                "example": {
                    "personalInfo": {
                        "name": "John Doe",
                        "email": "john@example.com"
                    },
                    "content": "Dear Hiring Manager,..."
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8501) 