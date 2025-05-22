import re
import subprocess
import os
import tempfile
from typing import Dict, Any

class ClassicResumeHelper:
    """
    Helper class for generating a Classic LaTeX resume from JSON data.
    Handles special characters: &, %, $, #
    """

    def __init__(self, data: Dict[str, Any]) -> None:
        """
        Initialize the ClassicResumeHelper class.

        Args:
            data (dict): The JSON data containing resume information.
        """
        self.data = self.replace_special_chars(data)
        self.output_path: str = "output.pdf"
        self.template_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_path = os.path.join(self.template_dir, "classic.tex")
        
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                self.template = f.read()
        except Exception as e:
            raise IOError(f"Error reading template file {self.template_path}: {e}") from e

        self.validate_data()

    def validate_data(self):
        """Ensure all required sections are present in the JSON data."""
        required_sections = [
            "personalInfo",
            "professionalSummary", 
            "education",
            "experience", 
            "projects", 
            "articlesAndPublications", 
            "achievements",
            "certifications", 
            "technologiesAndSkills"
        ]
        for section in required_sections:
            if section not in self.data:
                raise ValueError(f"Missing required section: {section}")
        
        # Validate personal info fields
        required_personal_info = [
            "name", 
            "email", 
            "phone", 
            "location",
            "website",
            "website_display",
            "linkedin",
            "linkedin_display"
        ]
        for field in required_personal_info:
            if field not in self.data["personalInfo"]:
                raise ValueError(f"Missing required personal info field: {field}")

    def replace_special_chars(self, data):
        """Recursively replace special LaTeX characters in strings."""
        if isinstance(data, str):
            return data.replace('&', r'\&') \
                       .replace('%', r'\%') \
                       .replace('$', r'\$') \
                       .replace('#', r'\#')
        if isinstance(data, list):
            return [self.replace_special_chars(item) for item in data]
        if isinstance(data, dict):
            return {k: self.replace_special_chars(v) for k, v in data.items()}
        return data

    def generate_personal_info(self):
        """Generate the Personal Information section."""
        # This is handled in the LaTeX template header section
        return ""

    def generate_professional_summary(self):
        """Generate the Professional Summary section."""
        return f"\\begin{{onecolentry}}{self.data['professionalSummary']}\\end{{onecolentry}}"

    def generate_education(self):
        """Generate the Education section."""
        sections = []
        for edu in self.data["education"]:
            entry = (
                f"\\textbf{{{edu['degree']}}} -- {edu['institution']} "
                f"\\hfill {edu.get('startDate', '')} -- {edu.get('endDate', '')}\n"
                "\\begin{highlights}\n"
                f"\\item \\textbf{{Focus:}} {edu.get('focus', '')}\n"
                f"\\item \\textbf{{Courses:}} {', '.join(edu['notableCourseWorks'])}\n"
                f"\\item \\textbf{{Projects:}} {', '.join(edu['projects'])}\n"
                "\\end{highlights}"
            )
            sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")
        return '\n'.join(sections)

    def generate_experience(self):
        """Generate the Experience section."""
        sections = []
        for exp in self.data["experience"]:
            start_date = exp.get('startDate', '')
            end_date = exp.get('endDate', 'Present')
            date_range = f"{start_date} -- {end_date}" if start_date else "Present"

            entry = (
                f"\\textbf{{{exp['title']}}}, {exp['company']} \\hfill {date_range}\n"
                "\\begin{highlights}\n"
                + '\n'.join([f"\\item {ach}" for ach in exp['achievements']])
                + "\n\\end{highlights}"
            )
            sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")
        return '\n'.join(sections)

    def generate_projects(self):
        """Generate the Projects section."""
        sections = []
        for proj in self.data["projects"]:
            desc_points = ', '.join([f"{desc}" for desc in proj['description']])  # Combine descriptions into a single line
            achievements = '\n'.join([f"\\item {ach}" for ach in proj['achievements']])
            
            entry = (
                f"\\textbf{{{proj['name']}}} - \\textit{{{desc_points}}}\n"  # Place description side by side with the name
                "\\begin{highlights}\n"
                f"\\item \\textbf{{Tools:}} {', '.join(proj['tools'])}\n"
                f"\\item \\textbf{{Achievements:}}\n"
                f"    \\begin{{itemize}}[leftmargin=*]\n"
                f"{achievements}\n"
                f"    \\end{{itemize}}\n"
                "\\end{highlights}"
            )
            sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")
        return '\n'.join(sections)

    def generate_articles_and_publications(self):
        """Generate the Articles & Publications section."""
        items = '\n'.join(
            f"\\item \\textbf{{{pub['title']}}} -- {pub['date']}" 
            for pub in self.data["articlesAndPublications"]
        )
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{items}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_achievements(self):
        """Generate the Achievements section."""
        bullets = '\n'.join(f"\\item {item}" for item in self.data["achievements"])
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{bullets}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_certifications(self):
        """Generate the Certifications section."""
        bullets = '\n'.join(f"\\item {item}" for item in self.data["certifications"])
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{bullets}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_technologies_and_skills(self):
        """Generate the Technologies & Skills section."""
        sections = []
        for skill in self.data["technologiesAndSkills"]:
            entry = f"\\textbf{{{skill['category']}}}: {', '.join(skill['skills'])}"
            sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")
        return '\n'.join(sections)

    def generate_resume(self):
        """Generate the final LaTeX resume by replacing placeholders."""
        info = self.data["personalInfo"]
        
        # Header replacements
        header_replacements = {
            "{{name}}": info["name"],
            "{{location}}": info["location"],
            "{{email}}": info["email"],
            "{{phone}}": info["phone"],
            "{{website}}": info["website"],
            "{{website_display}}": info["website_display"],
            "{{linkedin}}": info["linkedin"],
            "{{linkedin_display}}": info["linkedin_display"]
        }
        
        # Section replacements
        section_replacements = {
            "{{professional_summary}}": self.generate_professional_summary(),
            "{{education}}": self.generate_education(),
            "{{experience}}": self.generate_experience(),
            "{{projects}}": self.generate_projects(),
            "{{articles_and_publications}}": self.generate_articles_and_publications(),
            "{{achievements}}": self.generate_achievements(),
            "{{certifications}}": self.generate_certifications(),
            "{{technologies_and_skills}}": self.generate_technologies_and_skills(),
        }
        
        # Combine all replacements
        all_replacements = {**header_replacements, **section_replacements}
        
        resume = self.template
        for ph, content in all_replacements.items():
            resume = resume.replace(ph, content)

        if re.search(r"{{.*?}}", resume):
            raise ValueError("Unreplaced placeholders detected")
            
        return resume

    def export_to_pdf(self, output_path: str = "output.pdf") -> str:
        """Compile LaTeX content to PDF using pdflatex"""
        self.output_path = output_path
        content = self.generate_resume()

        with tempfile.TemporaryDirectory() as tmpdir:
            tex_path = os.path.join(tmpdir, "temp.tex")
            with open(tex_path, 'w', encoding='utf-8') as f:
                f.write(content)

            try:
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", f"-output-directory={tmpdir}", tex_path],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT
                )
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", f"-output-directory={tmpdir}", tex_path],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError("PDF compilation failed. Ensure pdflatex is installed.") from e

            pdf_path = os.path.join(tmpdir, "temp.pdf")
            if os.path.exists(pdf_path):
                os.replace(pdf_path, output_path)
            else:
                raise FileNotFoundError("PDF output not generated")
            
        return output_path
