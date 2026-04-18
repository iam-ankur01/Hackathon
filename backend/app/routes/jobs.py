"""Job matches + roadmap routes."""
from typing import List
from fastapi import APIRouter, Depends

from ..firebase import get_db
from ..security import get_current_user

router = APIRouter(prefix="/api", tags=["jobs"])


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
def roadmap(current=Depends(get_current_user)):
    """Personalized prep roadmap based on weakest category in latest report."""
    db = get_db()
    _all = [(d.id, d.to_dict()) for d in
            db.collection("interviews").where("user_id", "==", current["id"]).stream()]
    _all = [x for x in _all if (x[1] or {}).get("status") == "completed"]
    _all.sort(key=lambda x: (x[1] or {}).get("completed_at") or "", reverse=True)
    latest = _all[:1]

    weak_area = "answer_quality"
    if latest:
        cb = (latest[0][1] or {}).get("report", {}).get("category_breakdown", {})
        worst = None
        worst_pct = 1.0
        for key, val in cb.items():
            if isinstance(val, dict) and val.get("max"):
                pct = val["score"] / val["max"]
                if pct < worst_pct:
                    worst_pct = pct
                    worst = key
        if worst:
            weak_area = worst

    roadmaps = {
        "public_speaking": [
            {"week": 1, "goal": "Record 5-min daily answers; review pacing."},
            {"week": 2, "goal": "Practice tone variation drills."},
            {"week": 3, "goal": "Mock interview with a peer, focus on confidence."},
        ],
        "answer_quality": [
            {"week": 1, "goal": "Master STAR method with 10 past examples."},
            {"week": 2, "goal": "Deep-dive one system design topic per day."},
            {"week": 3, "goal": "Tailor answers to your top 3 target JDs."},
        ],
        "consistency_truthfulness": [
            {"week": 1, "goal": "Rewrite resume bullets with metrics + tech stack."},
            {"week": 2, "goal": "Populate GitHub READMEs for all pinned repos."},
            {"week": 3, "goal": "Align LinkedIn experience with resume."},
        ],
        "filler_word_assessment": [
            {"week": 1, "goal": "2-min daily silent pause practice."},
            {"week": 2, "goal": "Read aloud 10 min/day; mark fillers in transcript."},
            {"week": 3, "goal": "Record mock; target < 2 fillers/min."},
        ],
    }
    return {"focus_area": weak_area, "plan": roadmaps.get(weak_area, roadmaps["answer_quality"])}


@router.get("/coach")
def coach(current=Depends(get_current_user)):
    """Return coaching tips derived from latest interview."""
    db = get_db()
    _all = [(d.id, d.to_dict()) for d in
            db.collection("interviews").where("user_id", "==", current["id"]).stream()]
    _all = [x for x in _all if (x[1] or {}).get("status") == "completed"]
    _all.sort(key=lambda x: (x[1] or {}).get("completed_at") or "", reverse=True)
    latest = _all[:1]
    if not latest:
        return {"tips": [], "message": "Complete your first interview to unlock personalized coaching."}
    interview_id, data = latest[0]
    return {
        "interview_id": interview_id,
        "total_score": data.get("total_score"),
        "grade": data.get("grade"),
        "coaching": data.get("coaching", {}),
        "report_summary": data.get("report", {}).get("executive_summary", ""),
    }
