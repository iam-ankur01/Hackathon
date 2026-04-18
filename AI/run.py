"""
run.py — Quick-start script for the Interview Evaluator.
Modify the paths and parameters below, then run:
    python run.py
"""

from pipeline_v2 import evaluate_interview


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURE YOUR EVALUATION HERE
# ══════════════════════════════════════════════════════════════════════════════

# ── Session Data (per evaluation) ────────────────────────────────────────────
INTERVIEW_FILE = "interview.mp3"         # MP3, MP4, WAV, JSON, or TXT

JOB_DESCRIPTION = """
Software Engineer — Backend
Company: TechCorp Inc.

Requirements:
- 2+ years experience in Python, Go, or Java
- Experience with REST APIs and microservices
- Database design (PostgreSQL, MongoDB)
- CI/CD pipelines and cloud platforms (AWS/GCP)
- Strong problem-solving and communication skills
"""

# ── Profile Data (from signup/profile) ────────────────────────────────────────
RESUME_PATH = None          # e.g., "resume.pdf" or "resume.docx"
GITHUB_URL = None           # e.g., "https://github.com/johndoe" or just "johndoe"
LINKEDIN_URL = None         # e.g., "https://linkedin.com/in/johndoe" or just "johndoe"

# ══════════════════════════════════════════════════════════════════════════════
# RUN EVALUATION
# ══════════════════════════════════════════════════════════════════════════════

report = evaluate_interview(
    interview_path=INTERVIEW_FILE,
    job_description=JOB_DESCRIPTION,
    resume_path=RESUME_PATH,
    github_url=GITHUB_URL,
    linkedin_url=LINKEDIN_URL,
)

# Print the beautiful report
report.print_report()

# Save JSON
print(report.to_json())