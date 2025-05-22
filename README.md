# Resume Agent Template Engine

A powerful template engine for generating professional resumes and cover letters.

[![CI/CD](https://github.com/yourusername/resume-agent-template-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/resume-agent-template-engine/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/yourusername/resume-agent-template-engine/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/resume-agent-template-engine)

## Features

- **Multiple Template Support**: Choose from an expanding variety of professionally designed resume templates (e.g., Classic, Modern Minimalist, Two-Column) and cover letter templates.
- **Multiple Output Formats**: Generate documents in PDF (via LaTeX) and DOCX (for resumes).
- **Dynamic Content Generation**: Automatically generate content based on user input.
- **High-Quality Rendering**: LaTeX for PDF ensures professional typography; DOCX for broad compatibility.
- **RESTful API**: Easy integration with other applications.
- **Template Preview**: Preview templates before generating the final document (feature dependent on frontend).
- **Cover Letter Support**: Generate matching cover letters for your resume (currently PDF only).
- **Customizable Sections**: Add, remove, or modify sections as needed based on the data provided.

## Project Structure

The project structure is designed to be modular, allowing for easy addition of new templates.

```
resume-agent-template-engine/
├── src/
│   └── resume_agent_template_engine/
│       ├── core/
│       │   ├── docx_generator.py  # Handles DOCX generation
│       │   └── resume_template_editing.py # LaTeX/PDF related
│       ├── templates/
│       │   ├── resume/
│       │   │   └── [template_name]/  # e.g., classic, minimalist, twocolumn
│       │   │       ├── template.tex
│       │   │       ├── helper.py
│       │   │       ├── preview.png
│       │   │       └── README.md
│       │   └── cover_letter/
│       │       └── [template_name]/
│       │           ├── template.tex
│       │           ├── helper.py
│       │           ├── preview.png
│       │           └── README.md
│       ├── api/
│       │   └── app.py      # Main FastAPI application
│       └── ...
├── tests/
├── locustfile.py           # For performance testing
├── requirements.txt        # Main dependencies
├── requirements-dev.txt    # Development/testing dependencies
└── run.py                  # Script to run the FastAPI app
```

## System Requirements

- Python 3.8+
- **For PDF Generation**: A LaTeX distribution (MiKTeX, TeX Live, or MacTeX).
- Required Python packages (see `requirements.txt` and `requirements-dev.txt`).

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/resume-agent-template-engine.git
   cd resume-agent-template-engine
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt # For development and testing
   ```

4. **For PDF Generation**: Install LaTeX:
   - **Windows**: Install [MiKTeX](https://miktex.org/download)
   - **macOS**: Install [MacTeX](https://www.tug.org/mactex/)
   - **Linux**: Install TeX Live:
     ```bash
     sudo apt-get update && sudo apt-get install -y texlive-full
     ```
   (Note: `texlive-full` is comprehensive but large; smaller distributions like `texlive-latex-base`, `texlive-latex-recommended`, `texlive-fonts-recommended`, and `texlive-latex-extra` might suffice, depending on template needs.)

## Usage

1. Start the server:
   ```bash
   python run.py
   ```
   The API will typically be available at `http://localhost:8501`.

2. Access API Endpoints:
   - **Generate Document**: `POST /generate`
   - **List Templates**: `GET /templates`
   - **Health Check**: `GET /health`

3. Example API Request for Document Generation:
   The `/generate` endpoint is used for creating both resumes and cover letters. Specify the `document_type`, `template`, desired `format`, and the `data`.

   ```bash
   curl -X POST http://localhost:8501/generate \
     -H "Content-Type: application/json" \
     -d '{
       "document_type": "resume",
       "template": "minimalist",  # e.g., classic, minimalist, twocolumn
       "format": "docx",        # Use "pdf" or "docx" (docx for resumes only currently)
       "data": {
         "personalInfo": {"name": "John Doe", "email": "john.doe@example.com", "..."},
         "professional_summary": "Experienced professional...",
         "experience": [{...}, {...}],
         "education": [{...}],
         "projects": [{...}],
         "technologies_and_skills": ["Python", "FastAPI", "..."]
         // ... other fields as per the ResumeData model ...
       }
     }'
   ```
   **Note on `format` field**:
   - Use `"pdf"` to generate a PDF document using the specified LaTeX template.
   - Use `"docx"` to generate a Microsoft Word document (currently available for resumes only). The `template` field is still required in the request but is not used for styling the DOCX output in the same way as LaTeX templates.

## Output Formats

The engine supports the following output formats:

- **PDF**: Generated via LaTeX for high-quality, professional documents. Ideal for final versions and printing. Requires a LaTeX installation on the server.
- **DOCX**: Generated using `python-docx` for Microsoft Word documents. Useful for users who need to edit the resume content easily. Currently supported for resumes only.

## Template Format

Templates are organized by document type (resume, cover_letter) and then by template name (e.g., classic, minimalist, twocolumn). Each template directory typically contains:

- `template.tex`: The main LaTeX template file (for PDF generation).
- `helper.py`: Python helper class that populates the LaTeX template with data and handles PDF compilation. For DOCX, a separate generator (`docx_generator.py`) is used.
- `preview.png`: A preview image of the template.
- `README.md`: Template-specific documentation (optional).

New templates like "Modern Minimalist" and "Two-Column" follow this structure for their LaTeX/PDF components.

## Data Format

The template engine expects data in a structured JSON format. Key sections for a resume include: `personalInfo`, `professional_summary`, `experience`, `education`, `projects`, and `technologies_and_skills`. Refer to the Pydantic models in `src/resume_agent_template_engine/api/app.py` (e.g., `ResumeData`) for the detailed schema.

```json
{
  "document_type": "resume", // or "cover_letter"
  "template": "classic",    // e.g., classic, minimalist, twocolumn for resume
  "format": "pdf",          // "pdf" or "docx"
  "data": {
    "personalInfo": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "555-123-4567",
      "location": "New York, NY",
      "website": "johndoe.dev",
      "linkedin": "linkedin.com/in/johndoe"
    },
    "professional_summary": "A brief summary of your career.",
    "experience": [
      {
        "title": "Software Engineer",
        "company": "Tech Corp",
        "location": "San Francisco, CA",
        "startDate": "2020-01",
        "endDate": "Present",
        "details": ["Developed cool stuff.", "Led a team."]
      }
    ],
    "education": [
      {
        "degree": "B.S. in Computer Science",
        "institution": "University of Example",
        "location": "City, State",
        "date": "2020", // Or graduationYear
        "details": ["Relevant coursework or honors."]
      }
    ],
    "projects": [
      {
        "name": "My Awesome Project",
        "description": "A description of the project.",
        "technologies": ["Python", "FastAPI"]
      }
    ],
    "technologies_and_skills": ["Python", "JavaScript", "SQL"] 
    // Can also be a dictionary: {"Languages": ["Python"], "Frameworks": ["FastAPI"]}
    // ... other optional fields like 'articles_and_publications', 'certifications', 'achievements'
  }
}
```

## Development

The project uses GitHub Actions for continuous integration. The workflow includes:

- Running tests (Pytest).
- Code coverage reporting (Codecov).
- Linting with Black, Flake8, MyPy, and Pylint.

To contribute, please follow the guidelines in [CONTRIBUTING.md](CONTRIBUTING.md) and ensure pre-commit hooks are set up (`pre-commit install`).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.