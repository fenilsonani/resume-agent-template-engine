import pytest
from pydantic import ValidationError
from resume_agent_template_engine.api.app import ExperienceItem # Assuming models are in app.py

class TestExperienceItemValidation:

    def test_valid_dates(self):
        """Test ExperienceItem with valid startDate and endDate formats."""
        # Valid YYYY-MM
        item1 = ExperienceItem(
            title="Test Engineer",
            company="TestCo",
            startDate="2022-01",
            endDate="2023-01"
        )
        assert item1.startDate == "2022-01"
        assert item1.endDate == "2023-01"

        # Valid YYYY-MM-DD
        item2 = ExperienceItem(
            title="Test Engineer",
            company="TestCo",
            startDate="2022-01-15",
            endDate="2023-01-20"
        )
        assert item2.startDate == "2022-01-15"
        assert item2.endDate == "2023-01-20"

        # Valid endDate "Present"
        item3 = ExperienceItem(
            title="Test Engineer",
            company="TestCo",
            startDate="2022-01-15",
            endDate="Present"
        )
        assert item3.endDate == "Present"

    def test_invalid_start_date_format(self):
        """Test ExperienceItem with invalid startDate formats."""
        invalid_formats = [
            "01-2022",       # MM-YYYY
            "2022/01/15",    # YYYY/MM/DD
            "2022-1-1",      # YYYY-M-D (needs padding)
            "22-01-15",      # YY-MM-DD
            "January 2022",  # Full month name
            "20220115",      # No separators
            "2023-13-01",    # Invalid month
            "2023-02-30",    # Invalid day
            "2022",          # Year only
            "Present"        # "Present" is not valid for startDate
        ]
        for date_str in invalid_formats:
            with pytest.raises(ValidationError) as excinfo:
                ExperienceItem(
                    title="Test Engineer",
                    company="TestCo",
                    startDate=date_str,
                    endDate="2023-01-01"
                )
            assert "startDate" in str(excinfo.value).lower()
            assert "invalid date format" in str(excinfo.value).lower() or \
                   "ensure this value has at least 7 characters" in str(excinfo.value).lower() or \
                   "input should be a valid date" in str(excinfo.value).lower()


    def test_invalid_end_date_format(self):
        """Test ExperienceItem with invalid endDate formats (excluding 'Present')."""
        invalid_formats = [
            "01-2023",       # MM-YYYY
            "2023/01/15",    # YYYY/MM/DD
            "2023-1-1",      # YYYY-M-D
            "23-01-15",      # YY-MM-DD
            "February 2023", # Full month name
            "20230115",      # No separators
            "2023-13-01",    # Invalid month
            "2023-02-30"     # Invalid day
        ]
        for date_str in invalid_formats:
            with pytest.raises(ValidationError) as excinfo:
                ExperienceItem(
                    title="Test Engineer",
                    company="TestCo",
                    startDate="2022-01-01",
                    endDate=date_str
                )
            assert "endDate" in str(excinfo.value).lower()
            assert "invalid date format" in str(excinfo.value).lower() or \
                   "ensure this value has at least 7 characters" in str(excinfo.value).lower() or \
                   "input should be a valid date" in str(excinfo.value).lower()

    def test_end_date_present_is_valid(self):
        """Test that 'Present' is a valid endDate."""
        item = ExperienceItem(
            title="Current Role",
            company="Active Corp",
            startDate="2023-01-01",
            endDate="Present"
        )
        assert item.endDate == "Present"

    def test_missing_required_fields(self):
        """Test ExperienceItem with missing required fields (title, company, startDate, endDate)."""
        with pytest.raises(ValidationError) as excinfo:
            ExperienceItem(company="TestCo", startDate="2022-01", endDate="2023-01") # Missing title
        assert "title" in str(excinfo.value).lower()
        assert "field required" in str(excinfo.value).lower()

        with pytest.raises(ValidationError) as excinfo:
            ExperienceItem(title="Engineer", startDate="2022-01", endDate="2023-01") # Missing company
        assert "company" in str(excinfo.value).lower()
        assert "field required" in str(excinfo.value).lower()

        with pytest.raises(ValidationError) as excinfo:
            ExperienceItem(title="Engineer", company="TestCo", endDate="2023-01") # Missing startDate
        assert "startDate" in str(excinfo.value).lower()
        assert "field required" in str(excinfo.value).lower()

        with pytest.raises(ValidationError) as excinfo:
            ExperienceItem(title="Engineer", company="TestCo", startDate="2022-01") # Missing endDate
        assert "endDate" in str(excinfo.value).lower()
        assert "field required" in str(excinfo.value).lower()
    
    def test_optional_fields(self):
        """Test that optional fields (location, details) can be omitted or None."""
        item_minimal = ExperienceItem(
            title="Test Engineer",
            company="TestCo",
            startDate="2022-01",
            endDate="2023-01"
        )
        assert item_minimal.location is None
        assert item_minimal.details is None

        item_with_optionals = ExperienceItem(
            title="Test Engineer",
            company="TestCo",
            startDate="2022-01",
            endDate="2023-01",
            location="Remote",
            details=["Worked on X", "Implemented Y"]
        )
        assert item_with_optionals.location == "Remote"
        assert item_with_optionals.details == ["Worked on X", "Implemented Y"]

        item_with_null_optionals = ExperienceItem(
            title="Test Engineer",
            company="TestCo",
            startDate="2022-01",
            endDate="2023-01",
            location=None,
            details=None
        )
        assert item_with_null_optionals.location is None
        assert item_with_null_optionals.details is None
