import os
import importlib.util

class TemplateManager:
    """
    A class for managing and accessing different templates in the resume agent system.
    """
    _cached_templates = None
    
    def __init__(self, templates_dir="templates"):
        """
        Initialize the TemplateManager.
        
        Args:
            templates_dir (str): Path to the templates directory
        """
        self.templates_dir = templates_dir
        # Populate available_templates by calling get_available_templates,
        # which in turn uses the (now cached) _discover_templates method.
        self.available_templates = self.get_available_templates()

    def _discover_templates(self):
        """
        Discover available templates by scanning the templates directory.
        Caches the results to avoid redundant disk I/O.
        
        Returns:
            dict: A dictionary mapping template categories to template names
        """
        if TemplateManager._cached_templates is not None:
            return TemplateManager._cached_templates

        templates = {}
        
        # Check if templates directory exists
        if not os.path.exists(self.templates_dir):
            raise FileNotFoundError(f"Templates directory not found: {self.templates_dir}")
        
        # Scan for template categories (resume, cover_letter, etc.)
        for category in os.listdir(self.templates_dir):
            category_path = os.path.join(self.templates_dir, category)
            
            # Skip files and special directories
            if not os.path.isdir(category_path) or category.startswith('__'):
                continue
            
            templates[category] = []
            
            # Scan for template styles within each category
            for template_name in os.listdir(category_path):
                template_path = os.path.join(category_path, template_name)
                
                # Skip files and special directories
                if not os.path.isdir(template_path) or template_name.startswith('__'):
                    continue
                
                # Verify it has a helper.py file and a .tex file
                helper_path = os.path.join(template_path, "helper.py")
                tex_files = [f for f in os.listdir(template_path) if f.endswith('.tex')]
                
                if os.path.exists(helper_path) and tex_files:
                    templates[category].append(template_name)
        
        TemplateManager._cached_templates = templates
        return templates
    
    def get_available_templates(self, category=None):
        """
        Get available templates.
        
        Args:
            category (str, optional): The category to list templates for.
                                     If None, returns all categories and templates.
        
        Returns:
            dict or list: Available templates
        """
        # Ensure templates are discovered and cached if not already
        discovered_templates = self._discover_templates()

        if category:
            if category not in discovered_templates:
                raise ValueError(f"Category not found: {category}")
            return discovered_templates[category]
        
        return discovered_templates
    
    def load_template(self, category, template_name):
        """
        Load a template class by category and name.
        
        Args:
            category (str): The template category (e.g., 'resume', 'cover_letter')
            template_name (str): The name of the template
        
        Returns:
            class: The template class
        """
        # Ensure templates are discovered and available for validation
        current_available_templates = self.get_available_templates()

        # Validate category and template name
        if category not in current_available_templates:
            raise ValueError(f"Category not found: {category}")
        
        if template_name not in current_available_templates[category]:
            raise ValueError(f"Template not found: {template_name}")
        
        # Construct the path to the helper.py file
        helper_path = os.path.join(self.templates_dir, category, template_name, "helper.py")
        
        # Load the module dynamically
        spec = importlib.util.spec_from_file_location(f"{category}_{template_name}", helper_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Construct the expected class name based on the new convention
        # Category: 'cover_letter' -> 'CoverLetter'
        if "_" in category:
            category_camel_case = ''.join(x.capitalize() for x in category.split('_'))
        else:
            category_camel_case = category.capitalize()
        
        # Expected name: TemplateNameCategoryHelper, e.g., ModernResumeHelper
        expected_class_name = f"{template_name.capitalize()}{category_camel_case}Helper"
        
        try:
            template_class = getattr(module, expected_class_name)
            return template_class
        except AttributeError:
            # List all attributes in the module to help diagnose if the class exists with a slightly different name
            module_attributes = [name for name in dir(module) if not name.startswith('_')]
            raise ValueError(
                f"Helper class '{expected_class_name}' not found in module {helper_path}. "
                f"Ensure the class is defined in the helper file and matches this naming convention. "
                f"Available attributes in module: {module_attributes}"
            )
    
    def create_template(self, category, template_name, data):
        """
        Create a template instance with the provided data.
        
        Args:
            category (str): The template category (e.g., 'resume', 'cover_letter')
            template_name (str): The name of the template
            data (dict): The data to initialize the template with
        
        Returns:
            object: An instance of the template class
        """
        template_class = self.load_template(category, template_name)
        return template_class(data)
    
    def generate_pdf(self, category, template_name, data, output_path=None):
        """
        Generate a PDF from a template.
        
        Args:
            category (str): The template category (e.g., 'resume', 'cover_letter')
            template_name (str): The name of the template
            data (dict): The data to generate the document with
            output_path (str, optional): Path to save the PDF. If None, uses a default path.
        
        Returns:
            str: The path to the generated PDF
        """
        # Create the template instance
        template = self.create_template(category, template_name, data)
        
        # Set default output path if not provided
        if output_path is None:
            output_path = f"{category}_{template_name}.pdf"
        
        # Generate and export the document
        template.export_to_pdf(output_path)
        
        return output_path 