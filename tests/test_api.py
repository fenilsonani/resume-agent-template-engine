import pytest
from fastapi.testclient import TestClient
from resume_agent_template_engine.api.app import app
import json
import os
import shutil
from typing import Dict, Any
from copy import deepcopy

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_cleanup():
    """Setup test environment and cleanup after tests"""
    # Setup: Create necessary directories and files
    os.makedirs("templates/resume/modern", exist_ok=True)
    os.makedirs("templates/cover_letter/modern", exist_ok=True)
    
    # Create helper.py
    with open("templates/resume/modern/helper.py", "w") as f:
        f.write("""
class ModernResumeTemplate:
    def __init__(self, data):
        self.data = data
    
    def export_to_pdf(self, output_path):
        with open(output_path, 'w') as f:
            f.write("Test PDF content")
        return output_path
""")
    
    # Create template.tex
    with open("templates/resume/modern/template.tex", "w") as f:
        f.write(r"\documentclass{article}\begin{document}Test\end{document}")
    
    yield
    
    # Cleanup: Remove test files
    if os.path.exists("templates/resume/modern/helper.py"):
        os.remove("templates/resume/modern/helper.py")
    if os.path.exists("templates/resume/modern/template.tex"):
        os.remove("templates/resume/modern/template.tex")

# Test data
valid_resume_data = {
    "personalInfo": {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "location": "New York, NY",
        "website": "https://johndoe.com",
        "website_display": "johndoe.com",
        "linkedin": "https://linkedin.com/in/johndoe",
        "linkedin_display": "linkedin.com/in/johndoe"
    },
    "professionalSummary": "Experienced software engineer...",
    "education": [{
        "degree": "Bachelor of Science",
        "field": "Computer Science",
        "institution": "Example University",
        "graduationYear": "2020"
    }],
    "experience": [{
        "title": "Software Engineer",
        "company": "Tech Corp",
        "location": "San Francisco, CA",
        "startDate": "2020-01",
        "endDate": "Present",
        "highlights": ["Developed features", "Led team projects"]
    }],
    "projects": [{
        "name": "Project X",
        "description": "A cool project",
        "technologies": ["Python", "FastAPI"]
    }],
    "articlesAndPublications": [{
        "title": "Article 1",
        "publisher": "Tech Blog",
        "date": "2023"
    }],
    "achievements": ["Achievement 1", "Achievement 2"],
    "certifications": [{
        "name": "AWS Certified",
        "issuer": "Amazon",
        "date": "2023"
    }],
    "technologiesAndSkills": {
        "programming": ["Python", "JavaScript"],
        "frameworks": ["FastAPI", "React"],
        "tools": ["Git", "Docker"]
    }
}

# Test /health endpoint
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

# Test /templates endpoint
def test_list_templates():
    response = client.get("/templates")
    assert response.status_code == 200
    assert "templates" in response.json()
    templates = response.json()["templates"]
    assert isinstance(templates, dict)
    assert "resume" in templates
    assert "cover_letter" in templates

# Test /templates/{document_type} endpoint
def test_list_templates_by_valid_type():
    response = client.get("/templates/resume")
    assert response.status_code == 200
    assert "templates" in response.json()
    assert "modern" in response.json()["templates"]

def test_list_templates_by_invalid_type():
    response = client.get("/templates/invalid_type")
    assert response.status_code == 422  # Validation error for invalid enum

# Test /template-info/{document_type}/{template_name} endpoint
def test_get_template_info_valid():
    response = client.get("/template-info/resume/modern")
    assert response.status_code == 200
    assert "name" in response.json()
    assert "document_type" in response.json()
    assert response.json()["name"] == "modern"

def test_get_template_info_invalid_template():
    response = client.get("/template-info/resume/nonexistent_template")
    assert response.status_code == 404

# Test /schema/{document_type} endpoint
def test_get_schema_valid():
    response = client.get("/schema/resume")
    assert response.status_code == 200
    assert "schema" in response.json()
    assert "example" in response.json()

def test_get_schema_invalid_type():
    response = client.get("/schema/invalid_type")
    assert response.status_code == 422  # Validation error for invalid enum

# Test /generate endpoint
def test_generate_document_valid():
    request_data = {
        "document_type": "resume",
        "template": "modern",
        "format": "pdf",
        "data": valid_resume_data,
        "clean_up": True
    }
    response = client.post("/generate", json=request_data)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"

def test_generate_document_invalid_format():
    request_data = {
        "document_type": "resume",
        "template": "modern",
        "format": "doc",  # Invalid format
        "data": valid_resume_data,
        "clean_up": True
    }
    response = client.post("/generate", json=request_data)
    assert response.status_code == 400
    assert "Only PDF format is currently supported" in response.json()["detail"]

def test_generate_document_invalid_template():
    request_data = {
        "document_type": "resume",
        "template": "nonexistent_template",
        "format": "pdf",
        "data": valid_resume_data,
        "clean_up": True
    }
    response = client.post("/generate", json=request_data)
    assert response.status_code == 404
    assert "Template" in response.json()["detail"]

def test_generate_document_missing_required_data():
    invalid_data = {
        "document_type": "resume",
        "template": "modern",
        "format": "pdf",
        "data": {"personalInfo": {}},  # Missing required fields
        "clean_up": True
    }
    response = client.post("/generate", json=invalid_data)
    assert response.status_code == 400  # Bad Request for validation errors
    assert "required" in response.json()["detail"].lower()

def test_generate_document_null_values():
    data_with_nulls = deepcopy(valid_resume_data)
    data_with_nulls["personalInfo"]["website"] = None
    data_with_nulls["personalInfo"]["linkedin"] = None
    
    request_data = {
        "document_type": "resume",
        "template": "modern",
        "format": "pdf",
        "data": data_with_nulls,
        "clean_up": True
    }
    response = client.post("/generate", json=request_data)
    assert response.status_code == 200

def test_generate_document_empty_arrays():
    data_with_empty_arrays = deepcopy(valid_resume_data)
    data_with_empty_arrays["projects"] = []
    data_with_empty_arrays["achievements"] = []
    
    request_data = {
        "document_type": "resume",
        "template": "modern",
        "format": "pdf",
        "data": data_with_empty_arrays,
        "clean_up": True
    }
    response = client.post("/generate", json=request_data)
    assert response.status_code == 200

def test_input_validation_invalid_email():
    invalid_data = deepcopy(valid_resume_data)
    invalid_data["personalInfo"]["email"] = "invalid-email"
    
    request_data = {
        "document_type": "resume",
        "template": "modern",
        "format": "pdf",
        "data": invalid_data,
        "clean_up": True
    }
    response = client.post("/generate", json=request_data)
    assert response.status_code == 400  # Bad Request for validation errors
    assert "email" in response.json()["detail"].lower()

def test_input_validation_invalid_date():
    invalid_data = deepcopy(valid_resume_data)
    invalid_data["experience"][0]["startDate"] = "invalid-date"
    
    request_data = {
        "document_type": "resume",
        "template": "modern",
        "format": "pdf",
        "data": invalid_data,
        "clean_up": True
    }
    response = client.post("/generate", json=request_data)
    assert response.status_code == 400  # Bad Request for validation errors
    assert "date" in response.json()["detail"].lower()

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Resume Agent Template Engine"} 