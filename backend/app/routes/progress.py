"""Progress + dashboard aggregation routes."""
from collections import defaultdict
from fastapi import APIRouter, Depends

from ..firebase import get_db
from ..security import get_current_user

router = APIRouter(prefix="/api", tags=["progress"])


def _user_interviews(db, user_id: str, completed_only: bool = True):
    """Fetch interviews for a user, filter + sort in Python (no composite index needed)."""
    out = []
    for d in db.collection("interviews").where("user_id", "==", user_id).stream():
        data = d.to_dict() or {}
        if completed_only and data.get("status") != "completed":
            continue
        out.append({"id": d.id, **data})
    return out


@router.get("/dashboard")
def dashboard(current=Depends(get_current_user)):
    db = get_db()
    reports = _user_interviews(db, current["id"], completed_only=True)
    reports.sort(key=lambda r: r.get("completed_at") or "", reverse=True)
    reports = reports[:10]

    latest = reports[0] if reports else None
    latest_breakdown = (latest or {}).get("report", {}).get("category_breakdown", {})

    return {
        "hirescore": current.get("hirescore", 0),
        "total_interviews": len(reports),
        "latest_score": latest.get("total_score") if latest else None,
        "latest_grade": latest.get("grade") if latest else None,
        "latest_breakdown": latest_breakdown,
        "recent": [
            {
                "id": r["id"],
                "total_score": r.get("total_score"),
                "grade": r.get("grade"),
                "completed_at": r.get("completed_at"),
                "job_title": r.get("job_title"),
            }
            for r in reports[:5]
        ],
    }


@router.get("/progress")
def progress(current=Depends(get_current_user)):
    """Return score-over-time series + per-category averages."""
    db = get_db()
    reports = _user_interviews(db, current["id"], completed_only=True)
    reports.sort(key=lambda r: r.get("completed_at") or "")

    series = []
    cat_totals = defaultdict(list)
    for data in reports:
        series.append({"date": data.get("completed_at"), "score": data.get("total_score")})
        cb = data.get("report", {}).get("category_breakdown", {})
        for key, val in cb.items():
            if isinstance(val, dict) and "score" in val:
                cat_totals[key].append(val["score"])

    averages = {k: round(sum(v) / len(v), 1) for k, v in cat_totals.items() if v}
    return {"series": series, "category_averages": averages, "total": len(series)}
