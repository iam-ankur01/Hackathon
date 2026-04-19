"""Job matches + roadmap routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from ..firebase import get_db
from ..security import get_current_user
from ..services.ai_service import generate_roadmap, coach_chat

router = APIRouter(prefix="/api", tags=["jobs"])


class RoadmapPreferences(BaseModel):
    days: int = Field(..., ge=1, le=180)


class CoachChatTurn(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class CoachChatRequest(BaseModel):
    message: str
    history: List[CoachChatTurn] = []


def _latest_completed_interview(db, user_id: str):
    """Fetch the (id, data) of the user's most recent completed interview, or None."""
    rows = [(d.id, d.to_dict()) for d in
            db.collection("interviews").where("user_id", "==", user_id).stream()]
    rows = [x for x in rows if (x[1] or {}).get("status") == "completed"]
    rows.sort(key=lambda x: (x[1] or {}).get("completed_at") or "", reverse=True)
    return rows[0] if rows else None


_SEED_JOBS = [
    {"id": "j1", "title": "Software Engineer", "company": "Google",
     "location": "Bangalore", "skills": ["Python", "ML", "SQL"],
     "description": "Build scalable ML-powered products."},
    {"id": "j2", "title": "Frontend Engineer", "company": "Stripe",
     "location": "Remote", "skills": ["React", "TypeScript", "CSS"],
     "description": "Ship world-class payments UIs."},
    {"id": "j3", "title": "ML Engineer", "company": "OpenAI",
     "location": "San Francisco", "skills": ["Python", "PyTorch", "Deep Learning"],
     "description": "Train and deploy frontier models."},
    {"id": "j4", "title": "Full-Stack Developer", "company": "Razorpay",
     "location": "Bangalore", "skills": ["React", "Node.js", "SQL", "Python"],
     "description": "Build fintech infrastructure."},
    {"id": "j5", "title": "Data Scientist", "company": "Flipkart",
     "location": "Bangalore", "skills": ["Python", "SQL", "ML", "Statistics"],
     "description": "Drive product decisions with data."},
]


def _score_match(user_skills: List[str], job_skills: List[str]) -> float:
    if not job_skills:
        return 0.0
    us = {s.strip().lower() for s in user_skills if s.strip()}
    js = {s.strip().lower() for s in job_skills}
    overlap = us & js
    return round(len(overlap) / len(js) * 100, 1)


@router.get("/jobs")
def list_jobs(current=Depends(get_current_user)):
    db = get_db()
    jobs_col = db.collection("jobs")
    docs = list(jobs_col.limit(50).stream())
    jobs = [{**d.to_dict(), "id": d.id} for d in docs] if docs else _SEED_JOBS

    user_skills = (current.get("skills") or "").split(",")
    for j in jobs:
        j["match_score"] = _score_match(user_skills, j.get("skills", []))
    jobs.sort(key=lambda j: j.get("match_score", 0), reverse=True)
    return jobs


@router.get("/roadmap")
def roadmap(
    days: Optional[int] = Query(None, ge=1, le=180),
    current=Depends(get_current_user),
):
    """Personalized day-by-day prep roadmap.

    Uses the `days` query param, falling back to the user's saved `roadmap_days`,
    then defaulting to 30. Generates the plan from the latest completed interview's
    weakest categories via Groq Llama 3.3 70B (with a deterministic fallback).
    """
    db = get_db()
    latest = _latest_completed_interview(db, current["id"])
    if not latest:
        return {
            "days_requested": days or current.get("roadmap_days") or 30,
            "primary_focus": None,
            "summary": "Complete your first interview to unlock a personalized roadmap.",
            "days": [],
        }

    effective_days = days or current.get("roadmap_days") or 30
    effective_days = max(1, min(int(effective_days), 180))

    report = (latest[1] or {}).get("report", {}) or {}
    plan = generate_roadmap(report, effective_days)
    plan["days_requested"] = effective_days
    return plan


@router.post("/roadmap/preferences")
def save_roadmap_preferences(
    prefs: RoadmapPreferences,
    current=Depends(get_current_user),
):
    """Persist the user's preferred roadmap duration on their user doc."""
    db = get_db()
    db.collection("users").document(current["id"]).update({"roadmap_days": prefs.days})
    return {"roadmap_days": prefs.days}


@router.get("/coach")
def coach(current=Depends(get_current_user)):
    """Return coaching tips derived from latest interview."""
    db = get_db()
    latest = _latest_completed_interview(db, current["id"])
    if not latest:
        return {"tips": [], "message": "Complete your first interview to unlock personalized coaching."}
    interview_id, data = latest
    return {
        "interview_id": interview_id,
        "total_score": data.get("total_score"),
        "grade": data.get("grade"),
        "coaching": data.get("coaching", {}),
        "report_summary": data.get("report", {}).get("executive_summary", ""),
    }


@router.post("/coach/chat")
def coach_chat_endpoint(
    body: CoachChatRequest,
    current=Depends(get_current_user),
):
    """Grounded chat with the AI coach. Reply is based strictly on the latest report."""
    db = get_db()
    latest = _latest_completed_interview(db, current["id"])
    if not latest:
        return {"reply": "Complete your first interview so I can coach you with real data."}
    report = (latest[1] or {}).get("report", {}) or {}
    history = [t.model_dump() for t in body.history]
    reply = coach_chat(report, history, body.message)
    return {"reply": reply}
