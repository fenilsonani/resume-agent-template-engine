import pytest
import os
import shutil
from unittest import mock
from resume_agent_template_engine.templates.template_manager import TemplateManager

# Define a base path for test templates
TEST_TEMPLATES_DIR = "test_templates_dir"

@pytest.fixture(autouse=True)
def setup_and_teardown_test_environment():
    """Set up test template directories before each test and clean up after."""
    # Setup: Create base test templates directory
    os.makedirs(TEST_TEMPLATES_DIR, exist_ok=True)
    
    # Create dummy template structures
    # Valid resume template
    os.makedirs(os.path.join(TEST_TEMPLATES_DIR, "resume", "goodone"), exist_ok=True)
    with open(os.path.join(TEST_TEMPLATES_DIR, "resume", "goodone", "helper.py"), "w") as f:
        f.write("class GoodoneResumeHelper:\n    def __init__(self, data): pass\n    def export_to_pdf(self, path): pass")
    with open(os.path.join(TEST_TEMPLATES_DIR, "resume", "goodone", "template.tex"), "w") as f:
        f.write("Resume Test")

    # Resume template with bad helper name
    os.makedirs(os.path.join(TEST_TEMPLATES_DIR, "resume", "badhelpername"), exist_ok=True)
    with open(os.path.join(TEST_TEMPLATES_DIR, "resume", "badhelpername", "helper.py"), "w") as f:
        f.write("class BadNameResume:\n    def __init__(self, data): pass") # Wrong convention
    with open(os.path.join(TEST_TEMPLATES_DIR, "resume", "badhelpername", "template.tex"), "w") as f:
        f.write("Resume Test Bad Helper")

    # Resume template missing helper.py
    os.makedirs(os.path.join(TEST_TEMPLATES_DIR, "resume", "missinghelper"), exist_ok=True)
    with open(os.path.join(TEST_TEMPLATES_DIR, "resume", "missinghelper", "template.tex"), "w") as f:
        f.write("Resume Test Missing Helper")

    # Cover letter template
    os.makedirs(os.path.join(TEST_TEMPLATES_DIR, "cover_letter", "clgood"), exist_ok=True)
    with open(os.path.join(TEST_TEMPLATES_DIR, "cover_letter", "clgood", "helper.py"), "w") as f:
        f.write("class ClgoodCoverLetterHelper:\n    def __init__(self, data): pass\n    def export_to_pdf(self, path): pass")
    with open(os.path.join(TEST_TEMPLATES_DIR, "cover_letter", "clgood", "template.tex"), "w") as f:
        f.write("Cover Letter Test")

    # Dummy "minimalist" resume template
    os.makedirs(os.path.join(TEST_TEMPLATES_DIR, "resume", "minimalist"), exist_ok=True)
    with open(os.path.join(TEST_TEMPLATES_DIR, "resume", "minimalist", "helper.py"), "w") as f:
        f.write("class MinimalistResumeHelper:\n    def __init__(self, data): self.data = data\n    def export_to_pdf(self, path): open(path, 'w').write('Minimalist PDF')")
    with open(os.path.join(TEST_TEMPLATES_DIR, "resume", "minimalist", "template.tex"), "w") as f:
        f.write("Minimalist Resume Test")

    # Dummy "twocolumn" resume template
    os.makedirs(os.path.join(TEST_TEMPLATES_DIR, "resume", "twocolumn"), exist_ok=True)
    with open(os.path.join(TEST_TEMPLATES_DIR, "resume", "twocolumn", "helper.py"), "w") as f:
        f.write("class TwocolumnResumeHelper:\n    def __init__(self, data): self.data = data\n    def export_to_pdf(self, path): open(path, 'w').write('TwoColumn PDF')")
    with open(os.path.join(TEST_TEMPLATES_DIR, "resume", "twocolumn", "template.tex"), "w") as f:
        f.write("TwoColumn Resume Test")
        
    yield
    
    # Teardown: Remove the test templates directory
    shutil.rmtree(TEST_TEMPLATES_DIR)
    # Reset cache for other tests not using this fixture
    TemplateManager._cached_templates = None

# Minimal valid data for PDF generation tests
MINIMAL_RESUME_DATA = {
    "personalInfo": {"name": "Test User", "email": "test@example.com"},
    # Add other minimally required fields if your Pydantic models enforce them
    # For now, assuming only personalInfo is strictly needed by dummy helpers
}

class TestTemplateManager:

    def test_caching_of_discovered_templates(self):
        """Test that template discovery (filesystem scan) happens only once."""
        TemplateManager._cached_templates = None # Ensure cache is clear before test
        
        with mock.patch("os.listdir") as mocked_listdir:
            # Mock os.path.join to work with os.listdir mock
            def side_effect_join(path, *paths):
                if path == TEST_TEMPLATES_DIR:
                    return os.path.join(path, *paths) # Allow for category listing
                # For deeper paths, return something that os.path.isdir will see as a dir or file
                # This needs to be more nuanced if the test is to be more robust
                constructed_path = os.path.join(path, *paths)
                if "helper.py" in constructed_path or ".tex" in constructed_path:
                    return constructed_path # Treat as file
                return constructed_path # Treat as dir for simplicity

            mocked_listdir.return_value = ["resume", "cover_letter"] # Mock top-level categories
            
            # Further refine mock for sub-directories if necessary, or rely on os.path.exists/isdir mocks
            # For this test, primarily concerned about os.listdir on the base path.
            
            tm1 = TemplateManager(templates_dir=TEST_TEMPLATES_DIR)
            tm1.get_available_templates() # Initial discovery
            
            # Reset call count for the next check if os.listdir is called for each category
            # For simplicity, we check calls to the root templates_dir
            initial_call_count = mocked_listdir.call_count
            
            tm2 = TemplateManager(templates_dir=TEST_TEMPLATES_DIR)
            tm2.get_available_templates() # Should use cache
            
            tm3 = TemplateManager(templates_dir=TEST_TEMPLATES_DIR)
            tm3.get_available_templates("resume") # Should use cache
            
            # Assert os.listdir was called for the initial discovery.
            # The exact number of calls can be tricky depending on implementation details.
            # The key is that it doesn't increase with more TemplateManager instances or get_available_templates calls.
            assert mocked_listdir.call_count > 0, "os.listdir should have been called at least once."
            
            # Create a new instance and check again
            tm4 = TemplateManager(templates_dir=TEST_TEMPLATES_DIR)
            tm4.get_available_templates()
            
            # The number of calls to os.listdir should not have increased after the first full discovery.
            # This assumes _discover_templates caches effectively after the first successful scan.
            # If os.listdir is called per category, this assertion needs adjustment.
            # A more robust check might be to count calls to os.listdir(TEST_TEMPLATES_DIR) specifically.
            
            # Let's refine the assertion:
            # Count how many times os.listdir was called with TEST_TEMPLATES_DIR
            root_listdir_calls = 0
            for call_args in mocked_listdir.call_args_list:
                if call_args[0][0] == TEST_TEMPLATES_DIR:
                    root_listdir_calls +=1
            
            assert root_listdir_calls == 1, "os.listdir on the root template directory should only be called once."

    def test_load_template_success(self):
        """Test successful loading of a correctly named template helper."""
        TemplateManager._cached_templates = None # Clear cache
        tm = TemplateManager(templates_dir=TEST_TEMPLATES_DIR)
        template_class = tm.load_template("resume", "goodone")
        assert template_class.__name__ == "GoodoneResumeHelper"

    def test_load_template_bad_name_convention(self):
        """Test that loading a template with a helper class not following naming convention fails."""
        TemplateManager._cached_templates = None # Clear cache
        tm = TemplateManager(templates_dir=TEST_TEMPLATES_DIR)
        with pytest.raises(ValueError) as excinfo:
            tm.load_template("resume", "badhelpername")
        assert "Helper class 'BadhelpernameResumeHelper' not found" in str(excinfo.value)
        assert "BadNameResume" in str(excinfo.value) # Check if it lists available attributes

    def test_load_template_missing_helper_file(self):
        """Test loading a template where helper.py is missing."""
        TemplateManager._cached_templates = None # Clear cache
        tm = TemplateManager(templates_dir=TEST_TEMPLATES_DIR)
        # Temporarily remove helper.py for this test case if setup creates it by default for all
        helper_path = os.path.join(TEST_TEMPLATES_DIR, "resume", "missinghelper", "helper.py")
        if os.path.exists(helper_path): # Should not exist based on fixture
             os.remove(helper_path)

        with pytest.raises(FileNotFoundError) as excinfo: # spec_from_file_location will raise FileNotFoundError
            tm.load_template("resume", "missinghelper")
        assert "No such file or directory" in str(excinfo.value)
        assert helper_path in str(excinfo.value)


    def test_load_template_nonexistent_category(self):
        """Test loading a template from a non-existent category."""
        TemplateManager._cached_templates = None # Clear cache
        tm = TemplateManager(templates_dir=TEST_TEMPLATES_DIR)
        with pytest.raises(ValueError) as excinfo:
            tm.load_template("nonexistentcategory", "goodone")
        assert "Category not found: nonexistentcategory" in str(excinfo.value)

    def test_load_template_nonexistent_template_name(self):
        """Test loading a non-existent template from an existing category."""
        TemplateManager._cached_templates = None # Clear cache
        tm = TemplateManager(templates_dir=TEST_TEMPLATES_DIR)
        with pytest.raises(ValueError) as excinfo:
            tm.load_template("resume", "nosuchtemplate")
        assert "Template not found: nosuchtemplate" in str(excinfo.value)

    def test_get_available_templates_structure(self):
        """Test the structure of get_available_templates response."""
        TemplateManager._cached_templates = None # Clear cache
        tm = TemplateManager(templates_dir=TEST_TEMPLATES_DIR)
        templates = tm.get_available_templates()
        assert "resume" in templates
        assert "cover_letter" in templates
        assert "goodone" in templates["resume"]
        assert "badhelpername" in templates["resume"]
        # missinghelper should also be listed by _discover_templates as it has a .tex file
        assert "missinghelper" in templates["resume"]
        assert "minimalist" in templates["resume"] # Test discovery of minimalist
        assert "twocolumn" in templates["resume"]  # Test discovery of twocolumn
        assert "clgood" in templates["cover_letter"]

    def test_get_available_templates_specific_category(self):
        """Test getting available templates for a specific category."""
        TemplateManager._cached_templates = None # Clear cache
        tm = TemplateManager(templates_dir=TEST_TEMPLATES_DIR)
        resume_templates = tm.get_available_templates("resume")
        assert isinstance(resume_templates, list)
        assert "goodone" in resume_templates
        assert "badhelpername" in resume_templates
        assert "minimalist" in resume_templates
        assert "twocolumn" in resume_templates
        assert "clgood" not in resume_templates

    def test_get_available_templates_invalid_category(self):
        """Test getting available templates for an invalid category."""
        TemplateManager._cached_templates = None # Clear cache
        tm = TemplateManager(templates_dir=TEST_TEMPLATES_DIR)
        with pytest.raises(ValueError) as excinfo:
            tm.get_available_templates("invalidcategory")
        assert "Category not found: invalidcategory" in str(excinfo.value)

    @pytest.mark.parametrize("template_name", ["minimalist", "twocolumn", "goodone"])
    def test_basic_pdf_generation_for_new_templates(self, template_name, tmp_path):
        """Test basic PDF generation for newly added and existing valid templates."""
        TemplateManager._cached_templates = None # Clear cache
        tm = TemplateManager(templates_dir=TEST_TEMPLATES_DIR)
        
        output_pdf_file = tmp_path / f"{template_name}_test_resume.pdf"

        try:
            # Using the class-level MINIMAL_RESUME_DATA
            generated_path = tm.generate_pdf(
                category="resume",
                template_name=template_name,
                data=MINIMAL_RESUME_DATA, 
                output_path=str(output_pdf_file)
            )
            assert generated_path == str(output_pdf_file)
            assert output_pdf_file.exists()
            assert output_pdf_file.stat().st_size > 0 # Check if file is not empty
        finally:
            # Cleanup is handled by tmp_path fixture if file is within tmp_path
            # If not using tmp_path for output_pdf_file, then manual os.remove(output_pdf_file) is needed.
            pass 

# Ensure that the TemplateManager cache is reset if tests run in a different order
# or if some tests might pollute the global cache state.
# The autouse fixture should handle this for tests within this file.
# However, explicitly calling TemplateManager._cached_templates = None at the start/end
# of specific tests or test classes can provide more robustness if needed.
