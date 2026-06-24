"""User profile routes."""
import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from ..firebase import get_db, upload_file, delete_file
from ..schemas import ProfileUpdate
from ..security import get_current_user
from ..config import settings

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me")
def get_me(current=Depends(get_current_user)):
    return current


@router.patch("/me")
def update_me(update: ProfileUpdate, current=Depends(get_current_user)):
    db = get_db()
    updates = {k: v for k, v in update.model_dump().items() if v is not None}
    if not updates:
        return current
    db.collection("users").document(current["id"]).update(updates)
    doc = db.collection("users").document(current["id"]).get()
    data = doc.to_dict() or {}
    data["id"] = doc.id
    data.pop("password_hash", None)
    return data


@router.post("/me/resume")
async def upload_resume(file: UploadFile = File(...), current=Depends(get_current_user)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".pdf", ".docx", ".doc", ".txt"):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    local_name = f"{current['id']}_{uuid.uuid4().hex}{ext}"
    local_path = os.path.join(settings.UPLOAD_DIR, local_name)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The resume file is empty")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Resume files must be 10 MB or smaller")
    with open(local_path, "wb") as f:
        f.write(content)

    storage_uri = upload_file(local_path, dest_folder=f"resumes/{current['id']}")

    db = get_db()
    old_storage_uri = current.get("resume_storage_uri")
    db.collection("users").document(current["id"]).update({
        "resume_url": storage_uri,
        "resume_storage_uri": storage_uri,
        "resume_local_path": "" if storage_uri.startswith("gs://") else local_path,
        "resume_filename": file.filename,
    })
    if old_storage_uri and old_storage_uri != storage_uri:
        try:
            delete_file(old_storage_uri)
        except Exception:
            pass
    if storage_uri.startswith("gs://") and os.path.exists(local_path):
        os.remove(local_path)
    return {"resume_url": storage_uri, "resume_filename": file.filename}
