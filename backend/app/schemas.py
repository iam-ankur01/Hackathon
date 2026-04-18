"""Pydantic request/response schemas."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# ── Auth ──────────────────────────────────────────────────────────────────
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = None
    college: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


# ── Profile ───────────────────────────────────────────────────────────────
class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    role: Optional[str] = None
    level: Optional[str] = None
    college: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    gmail: Optional[str] = None
    skills: Optional[str] = None
    bio: Optional[str] = None


# ── Interview ─────────────────────────────────────────────────────────────
class InterviewSubmit(BaseModel):
    job_description: str = ""
    job_title: str = ""
    company_name: str = ""
    transcript_text: Optional[str] = None  # when user provides raw transcript


class InterviewSummary(BaseModel):
    id: str
    created_at: str
    total_score: float
    grade: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None


# ── Jobs ──────────────────────────────────────────────────────────────────
class JobPosting(BaseModel):
    id: str
    title: str
    company: str
    location: str
    description: str
    skills: List[str]
    match_score: Optional[float] = None
