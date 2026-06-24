"""Interview submission + results routes."""
import os
import sys
import io
import uuid
import contextlib
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks

from ..firebase import get_db, upload_file, download_file, delete_file
from ..security import get_current_user
from ..config import settings
from ..services.ai_service import run_pipeline, generate_coach_tips

router = APIRouter(prefix="/api/interviews", tags=["interviews"])

ALLOWED_AUDIO_EXT = {".mp3", ".mp4", ".mov", ".wav", ".m4a", ".webm", ".ogg", ".json", ".txt"}
MAX_UPLOAD_BYTES = 500 * 1024 * 1024


def _evaluate_and_save(interview_id: str, user_id: str, local_path: str,
                       media_storage_uri: Optional[str],
                       job_description: str, job_title: str, company_name: str,
                       resume_source: Optional[str],
                       github: Optional[str], linkedin: Optional[str],
                       transcript_text: Optional[str]):
    """Background task: run pipeline + persist result."""
    db = get_db()
    doc_ref = db.collection("interviews").document(interview_id)
    resume_path = resume_source
    downloaded_resume = None
    try:
        if resume_source and resume_source.startswith("gs://"):
            resume_ext = os.path.splitext(resume_source)[1] or ".pdf"
            downloaded_resume = os.path.join(
                settings.UPLOAD_DIR, f"resume_{uuid.uuid4().hex}{resume_ext}"
            )
            resume_path = download_file(resume_source, downloaded_resume)
        # Redirect pipeline's Unicode prints to a UTF-8 buffer so Windows
        # cp1252 console can't crash the background task.
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            report = run_pipeline(
                interview_path=local_path,
                job_description=job_description,
                job_title=job_title,
                company_name=company_name,
                resume_path=resume_path,
                github_url=github,
                linkedin_url=linkedin,
                transcript_text=transcript_text,
            )
        # Best-effort echo pipeline logs back to server console (safe-encoded)
        try:
            sys.stdout.write(buf.getvalue())
        except Exception:
            pass
        coaching = generate_coach_tips(report)
        # Extract the full transcript so the History view can show / export it.
        full_transcript = (
            (report.get("metadata") or {}).get("full_transcript")
            or transcript_text
            or ""
        )
        doc_ref.update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "report": report,
            "coaching": coaching,
            "total_score": report.get("total_score"),
            "grade": report.get("grade"),
            "transcript_text_full": full_transcript,
        })
        # Update user's rolling hirescore (simple average of last 5)
        recent = [r.to_dict() for r in
                  db.collection("interviews")
                  .where("user_id", "==", user_id).stream()
                  if r.to_dict().get("status") == "completed"]
        recent.sort(key=lambda r: r.get("completed_at", ""), reverse=True)
        recent = recent[:5]
        scores = [r.get("total_score", 0) for r in recent if r.get("total_score")]
        if scores:
            avg = round(sum(scores) / len(scores), 1)
            db.collection("users").document(user_id).update({"hirescore": avg})
    except Exception as e:
        doc_ref.update({"status": "failed", "error": str(e)})
    finally:
        if downloaded_resume and os.path.exists(downloaded_resume):
            os.remove(downloaded_resume)
        if settings.is_production and local_path and os.path.exists(local_path):
            os.remove(local_path)
        if settings.is_production and media_storage_uri:
            try:
                delete_file(media_storage_uri)
                doc_ref.update({
                    "audio_url": "",
                    "media_deleted_at": datetime.utcnow().isoformat(),
                })
            except Exception as cleanup_error:
                doc_ref.update({"media_cleanup_error": str(cleanup_error)})


@router.post("/")
async def submit_interview(
    background: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    transcript_text: Optional[str] = Form(None),
    job_description: str = Form(""),
    job_title: str = Form(""),
    company_name: str = Form(""),
    current=Depends(get_current_user),
):
    if not file and not transcript_text:
        raise HTTPException(status_code=400, detail="Provide either an audio/transcript file or transcript_text")

    local_path = None
    audio_url = None
    original_filename = None
    file_kind = None  # "audio" | "video" | "transcript"
    ext = ""
    if file:
        original_filename = file.filename or ""
        ext = os.path.splitext(original_filename)[1].lower()
        if ext not in ALLOWED_AUDIO_EXT:
            raise HTTPException(status_code=400, detail=f"Unsupported file type {ext}")
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        local_name = f"{current['id']}_{uuid.uuid4().hex}{ext}"
        local_path = os.path.join(settings.UPLOAD_DIR, local_name)
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=400,
                detail="The uploaded media file is empty. Choose a valid interview recording.",
            )
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail="The uploaded file exceeds the 500 MB size limit. Compress or trim it first.",
            )
        with open(local_path, "wb") as f:
            f.write(content)
        audio_url = upload_file(local_path, dest_folder=f"interviews/{current['id']}")
        if ext in (".mp4", ".mov", ".webm"):
            file_kind = "video"
        elif ext in (".json", ".txt"):
            file_kind = "transcript"
        else:
            file_kind = "audio"
    elif transcript_text:
        file_kind = "transcript"
        original_filename = "typed-transcript.txt"

    db = get_db()
    doc_ref = db.collection("interviews").document()
    doc_ref.set({
        "user_id": current["id"],
        "created_at": datetime.utcnow().isoformat(),
        "status": "processing",
        "job_description": job_description,
        "job_title": job_title,
        "company_name": company_name,
        "audio_url": audio_url,
        "has_transcript_text": bool(transcript_text),
        "original_filename": original_filename,
        "file_kind": file_kind,
        "file_ext": ext,
    })

    background.add_task(
        _evaluate_and_save,
        interview_id=doc_ref.id,
        user_id=current["id"],
        local_path=local_path or "",
        media_storage_uri=audio_url,
        job_description=job_description,
        job_title=job_title,
        company_name=company_name,
        resume_source=current.get("resume_storage_uri") or current.get("resume_local_path"),
        github=current.get("github"),
        linkedin=current.get("linkedin"),
        transcript_text=transcript_text,
    )

    return {"id": doc_ref.id, "status": "processing"}


@router.get("/")
def list_interviews(current=Depends(get_current_user)):
    db = get_db()
    docs = list(
        db.collection("interviews")
        .where("user_id", "==", current["id"])
        .stream()
    )
    out = []
    for d in docs:
        data = d.to_dict()
        out.append({
            "id": d.id,
            "created_at": data.get("created_at"),
            "status": data.get("status"),
            "total_score": data.get("total_score"),
            "grade": data.get("grade"),
            "job_title": data.get("job_title"),
            "company_name": data.get("company_name"),
        })
    out.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    return out[:50]


@router.get("/{interview_id}")
def get_interview(interview_id: str, current=Depends(get_current_user)):
    db = get_db()
    doc = db.collection("interviews").document(interview_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Not found")
    data = doc.to_dict()
    if data.get("user_id") != current["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    data["id"] = doc.id
    return data


@router.delete("/{interview_id}")
def delete_interview(interview_id: str, current=Depends(get_current_user)):
    db = get_db()
    ref = db.collection("interviews").document(interview_id)
    doc = ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Not found")
    data = doc.to_dict() or {}
    if data.get("user_id") != current["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    delete_file(data.get("audio_url", ""))
    ref.delete()
    return {"ok": True}
