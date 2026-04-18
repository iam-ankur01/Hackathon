"""Signup / login routes."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from ..firebase import get_db
from ..schemas import SignupRequest, LoginRequest, TokenResponse
from ..security import (
    hash_password, verify_password, create_access_token, get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_public(doc_id: str, data: dict) -> dict:
    data = {**data, "id": doc_id}
    data.pop("password_hash", None)
    return data


@router.post("/signup", response_model=TokenResponse)
def signup(req: SignupRequest):
    db = get_db()
    users = db.collection("users")
    # check email unique
    existing = list(users.where("email", "==", req.email.lower()).limit(1).stream())
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    doc_ref = users.document()
    payload = {
        "name": req.name,
        "email": req.email.lower(),
        "password_hash": hash_password(req.password),
        "role": req.role or "",
        "college": req.college or "",
        "created_at": datetime.utcnow().isoformat(),
        # profile defaults (editable from Profile page)
        "phone": "", "location": "", "level": "",
        "github": "", "linkedin": "", "gmail": req.email.lower(),
        "skills": "", "bio": "",
        "resume_url": "",
        "hirescore": 0,
    }
    doc_ref.set(payload)

    token = create_access_token(subject=doc_ref.id)
    return TokenResponse(access_token=token, user=_user_public(doc_ref.id, payload))


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    db = get_db()
    users = db.collection("users")
    found = list(users.where("email", "==", req.email.lower()).limit(1).stream())
    if not found:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    doc = found[0]
    data = doc.to_dict()
    if not verify_password(req.password, data.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(subject=doc.id)
    return TokenResponse(access_token=token, user=_user_public(doc.id, data))


@router.post("/token", response_model=TokenResponse)
def token_login(form: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 password-flow adapter (so Swagger UI `Authorize` works)."""
    return login(LoginRequest(email=form.username, password=form.password))


@router.get("/me")
def me(current=Depends(get_current_user)):
    return current
