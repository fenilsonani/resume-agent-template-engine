import os
import re
import subprocess
import tempfile
from typing import Dict, Any, List

class MinimalistResumeHelper:
    """
    Helper class for generating a 'Modern Minimalist' LaTeX resume from JSON data.
    """

    def __init__(self, data: Dict[str, Any]) -> None:
        """
        Initialize the MinimalistResumeHelper class.

        Args:
            data (dict): The JSON data containing resume information,
                         expected to conform to ResumeData Pydantic model structure.
        """
        self.data = self._escape_latex_special_chars_recursive(data)
        self.template_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_path = os.path.join(self.template_dir, "template.tex")

        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                self.latex_template_string = f.read()
        except Exception as e:
            raise IOError(f"Error reading template file {self.template_path}: {e}") from e

        self._validate_data() # Basic validation

    def _validate_data(self):
        """Ensure core data sections are present."""
        if "personalInfo" not in self.data:
            raise ValueError("Missing required section: personalInfo")
        # Add more specific field checks if necessary, though Pydantic handles this upstream.

    def _escape_latex_special_chars(self, text: str) -> str:
        """Escapes special LaTeX characters in a single string."""
        if not isinstance(text, str):
            return text
        chars = {
            '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
            '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
            '\\': r'\textbackslash{}', '<': r'\textless{}', '>': r'\textgreater{}',
        }
        for char, escaped_char in chars.items():
            text = text.replace(char, escaped_char)
        return text

    def _escape_latex_special_chars_recursive(self, data: Any) -> Any:
        """Recursively apply LaTeX escaping to strings within nested data structures."""
        if isinstance(data, str):
            return self._escape_latex_special_chars(data)
        elif isinstance(data, dict):
            return {k: self._escape_latex_special_chars_recursive(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._escape_latex_special_chars_recursive(item) for item in data]
        else:
            return data

    def _generate_personal_info(self) -> str:
        pi = self.data.get("personalInfo", {})
        name = pi.get("name", "Your Name")
        location = pi.get("location", "")
        phone = pi.get("phone", "")
        email = pi.get("email", "")
        website_display = pi.get("website_display", pi.get("website", "")) # Use website_display if available
        website_url = pi.get("website", "")

        # Constructing the contact line, filtering out empty parts
        contact_parts = [part for part in [location, phone, email, website_display if website_url else ""] if part]
        # For the LaTeX command, email and website need to be passed separately for \href
        
        # The \personalinfo command in LaTeX expects: {Name}{Location}{Phone}{Email}{Website URL for href, display text is part of contact_parts}
        # Let's adjust to match the new LaTeX command: \personalinfo{Name}{Location}{Phone}{Email}{Website URL}
        # The template.tex was: \personalinfo{Name}{Location \textperiodcentered\ Phone \textperiodcentered\ \href{mailto:Email}{Email} \textperiodcentered\ \href{WebsiteURL}{WebsiteDisplay}}
        # This means the helper should format the middle part.
        
        # For the new template.tex: \personalinfo{Name}{Location}{Phone}{Email}{WebsiteURL}
        # The LaTeX command itself will handle the formatting.
        return f"\\personalinfo{{{name}}}{{{location}}}{{{phone}}}{{{email}}}{{{website_url}}}"


    def _generate_summary(self) -> str:
        summary_text = self.data.get("professional_summary", "")
        if not summary_text:
            return ""
        return f"\\summary{{{summary_text}}}"

    def _generate_experience_section(self) -> str:
        experiences = self.data.get("experience", [])
        if not experiences:
            return ""
        
        section_content = ["\\section*{Experience}"]
        for exp in experiences:
            company = exp.get("company", "")
            title = exp.get("title", "")
            dates = f"{exp.get('startDate', '')} -- {exp.get('endDate', 'Present')}"
            location = exp.get("location", "")
            details_list = exp.get("details", [])
            
            details_latex = ""
            if details_list:
                details_latex = "\n".join([f"            \\item {self._escape_latex_special_chars(detail)}" for detail in details_list])
            
            # \experienceentry{Company}{Title}{Dates}{Location}{Details (list items)}
            section_content.append(f"\\experienceentry{{{company}}}{{{title}}}{{{dates}}}{{{location}}}{{\n{details_latex}\n        }}")
        return "\n".join(section_content)

    def _generate_education_section(self) -> str:
        educations = self.data.get("education", [])
        if not educations:
            return ""

        section_content = ["\\section*{Education}"]
        for edu in educations:
            degree = edu.get("degree", "")
            institution = edu.get("institution", "")
            # Assuming 'date' field for graduation year or date range
            dates = edu.get("date", edu.get("graduationYear", "")) 
            details = edu.get("details", []) # Assuming details might be a list
            
            details_latex = ""
            if isinstance(details, list) and details:
                details_latex = " ".join(details) # Simple join for now, or could be itemized
            elif isinstance(details, str):
                details_latex = details

            # \educationentry{Degree}{Institution}{Dates}{Details}
            section_content.append(f"\\educationentry{{{degree}}}{{{institution}}}{{{dates}}}{{{details_latex}}}")
        return "\n".join(section_content)

    def _generate_skills_section(self) -> str:
        skills_data = self.data.get("technologies_and_skills")
        if not skills_data:
            return ""

        skills_list = []
        if isinstance(skills_data, list): # e.g., ["Python", "JavaScript", "Data Analysis"]
            skills_list = skills_data
        elif isinstance(skills_data, dict): # e.g., {"Programming": ["Python", "Java"], "Databases": ["SQL"]}
            for category, skill_items in skills_data.items():
                skills_list.append(f"\\textbf{{{category}:}} {', '.join(skill_items)}")
            return f"\\skills{{{'; '.join(skills_list)}}}" # Join categories with semicolon or similar for clarity

        return f"\\skills{{{', '.join(skills_list)}}}"


    def _generate_projects_section(self) -> str:
        projects = self.data.get("projects", [])
        if not projects:
            return ""
        
        section_content = ["\\section*{Projects}"]
        for proj in projects:
            name = proj.get("name", "")
            technologies = ", ".join(proj.get("technologies", []))
            description = proj.get("description", "")
            # \projectentry{Name}{Technologies}{Description}
            section_content.append(f"\\projectentry{{{name}}}{{{technologies}}}{{{description}}}")
        return "\n".join(section_content)
    
    def _generate_publications_section(self) -> str:
        # Placeholder, implement if publications are part of ResumeData and template
        return ""

    def _generate_certifications_section(self) -> str:
        # Placeholder, implement if certifications are part of ResumeData and template
        return ""


    def generate_latex_content(self) -> str:
        """Generates the full LaTeX document content by populating placeholders."""
        
        # Replace placeholders in the main template string
        # \newcommand{\personalinfosection}{}
        # \newcommand{\summarysection}{}
        # \newcommand{\experiencesection}{}
        # \newcommand{\educationsection}{}
        # \newcommand{\skillssection}{}
        # \newcommand{\projectssection}{}

        populated_latex = self.latex_template_string

        replacements = {
            r"\newcommand{\personalinfosection}{}": self._generate_personal_info(),
            r"\newcommand{\summarysection}{}": self._generate_summary(),
            r"\newcommand{\experiencesection}{}": self._generate_experience_section(),
            r"\newcommand{\educationsection}{}": self._generate_education_section(),
            r"\newcommand{\skillssection}{}": self._generate_skills_section(),
            r"\newcommand{\projectssection}{}": self._generate_projects_section(),
            r"\newcommand{\publicationssection}{}": self._generate_publications_section(),
            r"\newcommand{\certificationssection}{}": self._generate_certifications_section(),
        }

        for placeholder_command, content_command in replacements.items():
            # We are replacing the definition of the command with the actual content command
            # So \newcommand{\personalinfosection}{} becomes \personalinfo{...details...}
            populated_latex = populated_latex.replace(placeholder_command, content_command if content_command else "")

        return populated_latex

    def export_to_pdf(self, output_path: str) -> str:
        """
        Generates the LaTeX content and compiles it to a PDF file.

        Args:
            output_path (str): The path where the generated PDF should be saved.
        
        Returns:
            str: The path to the generated PDF.
        """
        latex_content = self.generate_latex_content()
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with tempfile.TemporaryDirectory() as tmpdir:
            tex_file_path = os.path.join(tmpdir, "resume.tex")
            
            with open(tex_file_path, 'w', encoding='utf-8') as f:
                f.write(latex_content)

            compile_cmd = [
                "pdflatex",
                "-interaction=nonstopmode",
                "-output-directory=" + tmpdir,
                tex_file_path
            ]
            
            try:
                # Run twice to ensure cross-references (like ToC, page numbers) are correct if any
                subprocess.run(compile_cmd, check=True, capture_output=True, text=True, timeout=30)
                subprocess.run(compile_cmd, check=True, capture_output=True, text=True, timeout=30) 
            except subprocess.CalledProcessError as e:
                log_path = os.path.join(tmpdir, "resume.log")
                error_log = ""
                if os.path.exists(log_path):
                    with open(log_path, 'r', encoding='utf-8') as log_f:
                        error_log = log_f.read()
                raise RuntimeError(
                    f"PDF compilation failed with pdflatex.\n"
                    f"Command: {' '.join(e.cmd)}\n"
                    f"Return Code: {e.returncode}\n"
                    f"Stdout: {e.stdout}\n"
                    f"Stderr: {e.stderr}\n"
                    f"LaTeX Log (if available from {log_path}):\n{error_log}"
                ) from e
            except subprocess.TimeoutExpired as e:
                raise RuntimeError(f"PDF compilation timed out after {e.timeout} seconds.") from e

            generated_pdf_path = os.path.join(tmpdir, "resume.pdf")
            
            if os.path.exists(generated_pdf_path):
                shutil.move(generated_pdf_path, output_path)
            else:
                log_path = os.path.join(tmpdir, "resume.log")
                error_log = ""
                if os.path.exists(log_path):
                    with open(log_path, 'r', encoding='utf-8') as log_f:
                        error_log = log_f.read()
                raise FileNotFoundError(
                    f"PDF output file not found at {generated_pdf_path} after compilation. "
                    f"Check LaTeX logs for errors. Log content (if available):\n{error_log}"
                )
        return output_path

# Example usage (for testing the helper directly)
if __name__ == '__main__':
    import shutil # For shutil.move
    sample_data = {
        "personalInfo": {
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "phone": "123-456-7890",
            "location": "New York, NY",
            "website": "janedoe.dev",
            "linkedin": "linkedin.com/in/janedoe" # No Pydantic validation here, so full URL not enforced
        },
        "professional_summary": "Innovative and results-driven software engineer with 5+ years of experience in developing and scaling web applications. Proficient in Python, JavaScript, and cloud technologies. Seeking to leverage technical expertise and leadership skills to contribute to a dynamic organization.",
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "Tech Solutions Inc.",
                "location": "San Francisco, CA",
                "startDate": "2021-03",
                "endDate": "Present",
                "details": [
                    "Led a team of 5 engineers in developing new features for a SaaS platform, resulting in a 20% increase in user engagement.",
                    "Designed and implemented a microservices architecture using Docker and Kubernetes, improving system scalability and reliability.",
                    "Mentored junior engineers and conducted code reviews to maintain high code quality standards."
                ]
            },
            {
                "title": "Software Engineer",
                "company": "Web Innovations LLC",
                "location": "Austin, TX",
                "startDate": "2018-06",
                "endDate": "2021-02",
                "details": [
                    "Developed and maintained full-stack web applications using Python (Django/Flask) and JavaScript (React).",
                    "Contributed to the development of a RESTful API, improving data integration with third-party services.",
                    "Participated in Agile development processes, including sprint planning, daily stand-ups, and retrospectives."
                ]
            }
        ],
        "education": [
            {
                "degree": "Master of Science in Computer Science",
                "institution": "Stanford University",
                "location": "Stanford, CA",
                "date": "2018",
                "details": ["Focus on Artificial Intelligence. Thesis on Natural Language Processing."]
            },
            {
                "degree": "Bachelor of Science in Software Engineering",
                "institution": "University of Texas at Austin",
                "location": "Austin, TX",
                "date": "2016",
                "details": ["Graduated with Honors. Capstone project on mobile application development."]
            }
        ],
        "projects": [
            {
                "name": "Personal Portfolio Website",
                "technologies": ["React", "Next.js", "Vercel"],
                "description": "Developed a responsive personal portfolio website to showcase projects and skills. Integrated with a headless CMS for easy content management."
            },
            {
                "name": "Open Source Contribution: Awesome-Project",
                "technologies": ["Python", "Git"],
                "description": "Contributed to an open-source Python library by fixing bugs and adding new features. Collaborated with maintainers through GitHub."
            }
        ],
        "technologies_and_skills": { # Or could be a list: ["Python", "JavaScript", "AWS", "Docker", "Kubernetes", "SQL", "Git"]
            "Programming Languages": ["Python", "JavaScript", "Java", "C++"],
            "Frameworks & Libraries": ["Django", "Flask", "React", "Node.js", "Spring Boot"],
            "Databases": ["PostgreSQL", "MongoDB", "Redis"],
            "Cloud & DevOps": ["AWS", "Docker", "Kubernetes", "Terraform", "CI/CD"],
            "Other Skills": ["Agile Methodologies", "Problem Solving", "Team Leadership"]
        }
    }
    
    helper = MinimalistResumeHelper(sample_data)
    # latex_output = helper.generate_latex_content()
    # print("\n--- Generated LaTeX ---")
    # print(latex_output)
    # print("--- End LaTeX ---")

    output_pdf_path = "minimalist_resume_output.pdf"
    try:
        print(f"Generating PDF: {output_pdf_path}...")
        helper.export_to_pdf(output_pdf_path)
        print(f"PDF generated successfully: {output_pdf_path}")
    except Exception as e:
        print(f"Error generating PDF: {e}")

```
