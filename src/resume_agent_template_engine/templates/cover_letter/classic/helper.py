import re
import subprocess
import os
import tempfile
from typing import Dict, Any

class ClassicCoverLetterHelper:
    """
    Helper class for generating a Classic LaTeX cover letter from JSON data.
    Handles special characters: &, %, $, #
    """

    def __init__(self, data: Dict[str, Any]) -> None:
        """
        Initialize the ClassicCoverLetterHelper class.

        Args:
            data (dict): The JSON data containing cover letter information.
        """
        self.data = self.replace_special_chars(data)
        self.output_path: str = "output.pdf"
        self.template_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_path = os.path.join(self.template_dir, "modern.tex")
        
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                self.template = f.read()
        except Exception as e:
            raise IOError(f"Error reading template file {self.template_path}: {e}") from e

        self.validate_data()

    def validate_data(self):
        """Ensure all required sections are present in the JSON data."""
        # Check for required sections
        required_sections = [
            "personalInfo",
            "recipient",
            "date",
            "salutation",
            "body",
            "closing"
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
            "website_display"
        ]
        for field in required_personal_info:
            if field not in self.data["personalInfo"]:
                raise ValueError(f"Missing required personal info field: {field}")
        
        # Validate recipient
        if not isinstance(self.data["recipient"], dict):
            raise ValueError("Recipient must be a dictionary")
        
        # Check if body is a list of paragraphs
        if not isinstance(self.data["body"], list):
            raise ValueError("Body must be a list of paragraphs")

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

    def generate_recipient_address(self):
        """Format recipient information with LaTeX line breaks."""
        recipient = self.data['recipient']
        lines = [
            recipient.get('name', ''),
            recipient.get('title', ''),
            recipient.get('company', '')
        ]
        
        # Add address lines if present
        if 'address' in recipient and isinstance(recipient['address'], list):
            lines.extend(recipient['address'])
        
        # Filter out empty lines and join with LaTeX line break
        return ' \\\\\n'.join(filter(None, lines))

    def generate_cover_letter(self):
        """Generate the final LaTeX cover letter by replacing placeholders."""
        info = self.data["personalInfo"]
        
        # Header replacements
        header_replacements = {
            "{{name}}": info["name"],
            "{{location}}": info["location"],
            "{{email}}": info["email"],
            "{{phone}}": info["phone"],
            "{{website}}": info["website"],
            "{{website_display}}": info["website_display"]
        }
        
        # Content replacements
        content_replacements = {
            "{{recipient_address}}": self.generate_recipient_address(),
            "{{date}}": self.data["date"],
            "{{salutation}}": self.data["salutation"],
            "{{body_content}}": '\n\n'.join(self.data["body"]),
            "{{closing}}": self.data["closing"]
        }
        
        # Combine all replacements
        all_replacements = {**header_replacements, **content_replacements}
        
        cover_letter = self.template
        for placeholder, content in all_replacements.items():
            cover_letter = cover_letter.replace(placeholder, content)
        
        # Check for unreplaced placeholders
        if re.search(r"{{.*?}}", cover_letter):
            raise ValueError("Unreplaced placeholders detected")
        
        return cover_letter

    def export_to_pdf(self, output_path: str = "output.pdf") -> str:
        """Compile LaTeX content to PDF using pdflatex"""
        self.output_path = output_path
        content = self.generate_cover_letter()
        
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