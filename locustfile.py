import random
from locust import HttpUser, task, between

class ResumeApiUser(HttpUser):
    # Users will wait 1 to 3 seconds between tasks
    wait_time = between(1, 3)

    # Minimal valid resume data payload for the /generate endpoint
    # Uses the "classic" resume template
    sample_resume_data = {
        "personalInfo": {
            "name": "Locust Test User",
            "email": "locust.user@example.com",
            "phone": "555-1234",
            "location": "Test City, TS",
            "website": "example.com",
            "linkedin": "linkedin.com/in/locustuser"
        },
        "professional_summary": "A dedicated load testing professional.",
        "experience": [
            {
                "title": "Chief Load Generator",
                "company": "The Swarm Inc.",
                "location": "Cloud City",
                "startDate": "2023-01", # YYYY-MM format
                "endDate": "Present",
                "details": [
                    "Generated significant load.",
                    "Identified several bottlenecks."
                ]
            }
        ],
        "education": [
            {
                "degree": "B.Sc. Computer Science",
                "institution": "University of Testing",
                "location": "Testville",
                "date": "2022" # Or "2020-05" / "2020-05-15"
            }
        ],
        "projects": [
            {
                "name": "API Benchmark",
                "description": "A project to benchmark this very API."
            }
        ],
        "technologies_and_skills": ["Python", "Locust", "FastAPI"]
        # Other optional fields like articles_and_publications, achievements, certifications can be added if needed
    }

    @task(1) # Lower weight, less frequent
    def health_check(self):
        """Task to hit the /health endpoint."""
        self.client.get("/health", name="/health")

    @task(5) # Medium weight
    def list_templates(self):
        """Task to hit the /templates endpoint."""
        self.client.get("/templates", name="/templates")

    @task(10) # Higher weight, most frequent critical path
    def generate_resume_document(self):
        """Task to hit the /generate endpoint for a resume."""
        payload = {
            "document_type": "resume",
            "template": "classic", # Assuming 'classic' is a valid resume template
            "format": "pdf",
            "data": self.sample_resume_data,
            "clean_up": True
        }
        self.client.post("/generate", json=payload, name="/generate (resume)")

    # Example of how to add a cover letter generation task if needed
    # @task(3)
    # def generate_cover_letter_document(self):
    #     """Task to hit the /generate endpoint for a cover letter."""
    #     # Ensure sample_cover_letter_data is defined similarly to sample_resume_data
    #     # and that a valid cover letter template exists (e.g., "classic_cl")
    #     cover_letter_payload = {
    #         "document_type": "cover_letter",
    #         "template": "classic", # Replace with actual cover letter template name
    #         "format": "pdf",
    #         "data": { # Simplified data for cover letter
    #             "personalInfo": {
    #                 "name": "Locust Test User",
    #                 "email": "locust.user@example.com"
    #             },
    #             "recipient": {
    #                 "name": "Hiring Manager"
    #             },
    #             "date": "2024-07-26",
    #             "salutation": "Dear Hiring Manager,",
    #             "body": ["This is a test cover letter body."],
    #             "closing": "Sincerely,"
    #         },
    #         "clean_up": True
    #     }
    #     self.client.post("/generate", json=cover_letter_payload, name="/generate (cover_letter)")

    def on_start(self):
        """
        Called when a Locust start before any task is scheduled.
        Can be used for login or other setup.
        """
        print("Starting new Locust user...")

    def on_stop(self):
        """
        Called when a Locust stops.
        """
        print("Stopping Locust user...")
