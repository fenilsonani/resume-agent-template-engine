import os
import re
import subprocess
import tempfile
import shutil # For shutil.move
from typing import Dict, Any, List

class TwocolumnResumeHelper:
    """
    Helper class for generating a 'Two-Column' LaTeX resume from JSON data.
    """

    def __init__(self, data: Dict[str, Any]) -> None:
        """
        Initialize the TwocolumnResumeHelper class.

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

        self._validate_data()

    def _validate_data(self):
        """Ensure core data sections are present."""
        if "personalInfo" not in self.data:
            raise ValueError("Missing required section: personalInfo")

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

    def _generate_name_header(self) -> str:
        pi = self.data.get("personalInfo", {})
        name = pi.get("name", "Your Name")
        return f"\\nameheader{{{name}}}"

    def _generate_left_column_content(self) -> str:
        """Generates LaTeX for the entire left column."""
        content = []
        
        # Contact Info
        pi = self.data.get("personalInfo", {})
        email = pi.get("email", "")
        phone = pi.get("phone", "")
        linkedin_url = pi.get("linkedin", "") # Assuming full URL
        website_url = pi.get("website", "")   # Assuming full URL
        content.append(f"\\contactinfo{{{email}}}{{{phone}}}{{{linkedin_url}}}{{{website_url}}}")

        # Skills
        skills_data = self.data.get("technologies_and_skills")
        if skills_data:
            skills_latex = ""
            if isinstance(skills_data, list):
                skills_latex = ", ".join(skills_data)
            elif isinstance(skills_data, dict): # Category-based skills
                temp_skills_list = []
                for category, skill_items in skills_data.items():
                    temp_skills_list.append(f"\\textbf{{{self._escape_latex_special_chars(category)}}}: {', '.join(map(self._escape_latex_special_chars, skill_items))}")
                skills_latex = "\\newline ".join(temp_skills_list) # Use newline or adjust LaTeX command
            if skills_latex:
                 content.append(f"\\skillslist{{{skills_latex}}}")
        
        # Education (Summary in Left Column)
        educations = self.data.get("education", [])
        if educations:
            edu_items_latex = []
            for edu in educations:
                degree = edu.get("degree", "")
                institution = edu.get("institution", "")
                dates = edu.get("date", edu.get("graduationYear", ""))
                edu_items_latex.append(f"\\educationentryleft{{{degree}}}{{{institution}}}{{{dates}}}")
            content.append(f"\\educationlistleft{{\n{chr(10).join(edu_items_latex)}\n}}")

        return "\n".join(content)

    def _generate_right_column_content(self) -> str:
        """Generates LaTeX for the entire right column."""
        content = []

        # Summary
        summary_text = self.data.get("professional_summary", "")
        if summary_text:
            content.append(f"\\summarysectioncontent{{{summary_text}}}")

        # Experience
        experiences = self.data.get("experience", [])
        if experiences:
            content.append("\\section*{Experience}")
            for exp in experiences:
                title = exp.get("title", "")
                company = exp.get("company", "")
                dates = f"{exp.get('startDate', '')} -- {exp.get('endDate', 'Present')}"
                location = exp.get("location", "")
                details_list = exp.get("details", [])
                details_latex = "\n".join([f"            \\item {detail}" for detail in details_list]) # Already escaped
                content.append(f"\\experienceentryright{{{title}}}{{{company}}}{{{dates}}}{{{location}}}{{\n{details_latex}\n        }}")
        
        # Projects
        projects = self.data.get("projects", [])
        if projects:
            content.append("\\section*{Projects}")
            for proj in projects:
                name = proj.get("name", "")
                technologies = ", ".join(proj.get("technologies", [])) # Already escaped if list of strings
                description = proj.get("description", "") # Already escaped
                content.append(f"\\projectsentryright{{{name}}}{{{technologies}}}{{{description}}}")
        
        # Optionally add publications, certifications if they fit better in the right column
        # For example:
        # publications = self.data.get("articles_and_publications", [])
        # if publications:
        #     content.append("\\section*{Publications}")
        #     for pub in publications:
        #         # Format publication entry for right column
        #         content.append(f"\\publicationentryright...")


        return "\n\n".join(content)


    def generate_latex_content(self) -> str:
        """Generates the full LaTeX document content by populating placeholders."""
        
        populated_latex = self.latex_template_string

        replacements = {
            r"\newcommand{\nameplaceholder}{}": self._generate_name_header(),
            r"\newcommand{\leftcolumncontent}{}": self._generate_left_column_content(),
            r"\newcommand{\rightcolumncontent}{}": self._generate_right_column_content(),
        }

        for placeholder_command, content_command in replacements.items():
            populated_latex = populated_latex.replace(placeholder_command, content_command if content_command else "")
            
        return populated_latex

    def export_to_pdf(self, output_path: str) -> str:
        """
        Generates the LaTeX content and compiles it to a PDF file.
        """
        latex_content = self.generate_latex_content()
        
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
    sample_data = {
        "personalInfo": {
            "name": "John Q. Public",
            "email": "john.public@email.com",
            "phone": "555-0101",
            "location": "Anytown, USA", # Not directly used in left col contact, but good to have
            "website": "https://jqpublic.dev",
            "linkedin": "https://linkedin.com/in/jqpublic"
        },
        "professional_summary": "Dynamic and detail-oriented professional with extensive experience in software development and project management. Proven ability to lead teams and deliver high-quality products on time and within budget. Seeking a challenging role in a forward-thinking company.",
        "experience": [
            {
                "title": "Senior Project Manager",
                "company": "Innovatech Solutions",
                "location": "Tech City, CA",
                "startDate": "2020-01",
                "endDate": "Present",
                "details": [
                    "Managed a portfolio of 10+ software projects, ensuring alignment with strategic goals.",
                    "Implemented Agile methodologies, improving team productivity by 25%.",
                    "Successfully delivered three major products to market, generating over $5M in revenue."
                ]
            },
            {
                "title": "Software Developer",
                "company": "CodeCrafters Ltd.",
                "location": "Logic Lane, MA",
                "startDate": "2017-06",
                "endDate": "2019-12",
                "details": [
                    "Developed and maintained web applications using Python, Django, and JavaScript.",
                    "Collaborated with cross-functional teams to define project requirements and deliverables.",
                    "Contributed to a 15% reduction in bug reports through rigorous testing and code reviews."
                ]
            }
        ],
        "education": [
            {
                "degree": "M.S. in Computer Science",
                "institution": "State University",
                "location": "Capital City", # Not used in left column summary
                "date": "2017",
                "details": ["Thesis on AI-driven data analytics."] # Not used in left column summary
            },
            {
                "degree": "B.S. in Information Technology",
                "institution": "Community College",
                "location": "Hometown",
                "date": "2015",
                "details": ["Graduated Summa Cum Laude."]
            }
        ],
        "projects": [
            {
                "name": "AI-Powered Chatbot",
                "technologies": ["Python", "NLTK", "TensorFlow"],
                "description": "Developed a customer service chatbot that reduced response times by 40%."
            },
            {
                "name": "E-commerce Platform Optimization",
                "technologies": ["Magento", "PHP", "MySQL"],
                "description": "Optimized database queries and caching mechanisms, improving site speed by 30%."
            }
        ],
         "technologies_and_skills": {
            "Languages": ["Python", "JavaScript", "SQL", "Java"],
            "Frameworks": ["Django", "Flask", "React", "Spring"],
            "Tools": ["Git", "Docker", "Kubernetes", "JIRA"],
            "Methodologies": ["Agile", "Scrum", "Waterfall"]
        }
    }
    
    helper = TwocolumnResumeHelper(sample_data)
    output_pdf_path = "twocolumn_resume_output.pdf"
    try:
        print(f"Generating PDF: {output_pdf_path}...")
        helper.export_to_pdf(output_pdf_path)
        print(f"PDF generated successfully: {output_pdf_path}")
    except Exception as e:
        print(f"Error generating PDF: {e}")

```
