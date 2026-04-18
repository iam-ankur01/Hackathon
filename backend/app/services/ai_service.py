"""Wrap the AI interview evaluation pipeline."""
import os
import sys
from typing import Optional

# Make the AI/ folder importable
_AI_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "AI"))
if _AI_DIR not in sys.path:
    sys.path.insert(0, _AI_DIR)


def run_pipeline(
    interview_path: str,
    job_description: str = "",
    job_title: str = "",
    company_name: str = "",
    resume_path: Optional[str] = None,
    github_url: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    transcript_text: Optional[str] = None,
) -> dict:
    """Run the full evaluation pipeline and return a serializable report dict."""
    from pipeline_v2 import evaluate_interview  # lazy import

    report = evaluate_interview(
        interview_path=interview_path,
        job_description=job_description,
        job_title=job_title,
        company_name=company_name,
        resume_path=resume_path,
        github_url=github_url,
        linkedin_url=linkedin_url,
        transcript_text=transcript_text,
    )
    return report.to_dict()


def generate_coach_tips(report: dict) -> dict:
    """Given a scoring report, produce actionable coaching suggestions."""
    cat = report.get("category_breakdown", {})
    tips = []
    if cat.get("filler_word_assessment", {}).get("score", 10) < 7:
        tips.append({
            "area": "Filler Words",
            "tip": "Practice pausing instead of saying 'um' or 'like'. Record yourself for 2 min daily.",
        })
    if cat.get("public_speaking", {}).get("score", 30) < 20:
        tips.append({
            "area": "Public Speaking",
            "tip": "Work on pacing and confident tone — try the STAR method for structured answers.",
        })
    if cat.get("answer_quality", {}).get("score", 40) < 28:
        tips.append({
            "area": "Answer Quality",
            "tip": "Directly address the question first, then support with examples tied to the job description.",
        })
    if cat.get("consistency_truthfulness", {}).get("score", 20) < 14:
        tips.append({
            "area": "Consistency",
            "tip": "Align stories with your resume and GitHub — use real project names and concrete numbers.",
        })
    return {
        "tips": tips,
        "improvement_areas": report.get("areas_for_improvement", []),
        "strengths": report.get("strengths", []),
    }
