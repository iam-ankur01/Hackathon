"""History routes — per-user upload/record history with transcripts.

Every submission to POST /api/interviews/ automatically creates a history
entry (same Firestore document). These endpoints expose a simplified,
history-shaped view of those documents so the frontend can list, search,
preview, and delete them without leaking the full scoring report.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from ..firebase import get_db
from ..security import get_current_user

router = APIRouter(prefix="/api/history", tags=["history"])


def _to_history_row(doc_id: str, data: dict) -> dict:
    """Flatten an interviews doc into a history-row shape."""
    data = data or {}
    # Fallback transcript for older docs that predate persistence.
    transcript = (
        data.get("transcript_text_full")
        or (data.get("report") or {}).get("metadata", {}).get("full_transcript")
        or ""
    )
    return {
        "id": doc_id,
        "filename": data.get("original_filename") or "(untitled)",
        "file_kind": data.get("file_kind") or "audio",
        "file_ext": data.get("file_ext") or "",
        "created_at": data.get("created_at") or "",
        "completed_at": data.get("completed_at") or "",
        "status": data.get("status") or "processing",
        "total_score": data.get("total_score"),
        "grade": data.get("grade"),
        "job_title": data.get("job_title") or "",
        "company_name": data.get("company_name") or "",
        "transcript": transcript,
        "transcript_available": bool(transcript),
        "transcript_word_count": len(transcript.split()) if transcript else 0,
    }


@router.get("")
def list_history(current=Depends(get_current_user)):
    """Return every interview owned by the current user, newest first."""
    db = get_db()
    rows = [
        _to_history_row(d.id, d.to_dict())
        for d in db.collection("interviews")
        .where("user_id", "==", current["id"])
        .stream()
    ]
    rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    return rows


@router.delete("/{history_id}")
def delete_history_entry(history_id: str, current=Depends(get_current_user)):
    """Delete one history entry (also removes the underlying interview doc)."""
    db = get_db()
    ref = db.collection("interviews").document(history_id)
    snap = ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Not found")
    data = snap.to_dict() or {}
    if data.get("user_id") != current["id"]:
        raise HTTPException(status_code=403, detail="Not your entry")
    ref.delete()
    return {"deleted": history_id}
