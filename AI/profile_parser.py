"""
profile_parser.py
Extracts and structures candidate profile data from Resume, GitHub, and LinkedIn.

Handles:
  - Resume parsing (PDF/DOCX → structured text extraction)
  - GitHub profile scraping (repos, languages, contributions)
  - LinkedIn profile scraping (experience, skills, education)
  - AI-powered profile synthesis for cross-verification
"""

import os
import re
import json
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from groq import Groq


@dataclass
class ResumeData:
    raw_text: str
    skills: List[str]
    experience_summary: str
    education: str
    projects: List[str]
    certifications: List[str]
    total_years_experience: Optional[float]


@dataclass
class GitHubData:
    username: str
    profile_url: str
    bio: str
    repos: List[Dict]           # [{name, description, language, stars}]
    top_languages: List[str]
    total_repos: int
    contribution_summary: str
    raw_text: str               # full scraped text for AI analysis


@dataclass
class LinkedInData:
    profile_url: str
    headline: str
    summary: str
    experience: List[Dict]      # [{title, company, duration, description}]
    skills: List[str]
    education: List[Dict]       # [{institution, degree, field}]
    raw_text: str               # full scraped text for AI analysis


@dataclass
class CandidateProfile:
    resume: Optional[ResumeData]
    github: Optional[GitHubData]
    linkedin: Optional[LinkedInData]
    synthesized_summary: str    # AI-generated unified profile summary
    claimed_skills: List[str]   # all skills from all sources
    claimed_experience: str     # unified experience narrative
    verification_notes: List[str]  # discrepancies or notable points


# ── Resume Parsing ────────────────────────────────────────────────────────────

def _extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber or PyPDF2."""
    text = ""

    # Try pdfplumber first (better formatting)
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        if text.strip():
            return text.strip()
    except ImportError:
        pass

    # Fallback to PyPDF2
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
        if text.strip():
            return text.strip()
    except ImportError:
        pass

    # Final fallback: try pdftotext (system command)
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", pdf_path, "-"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    raise RuntimeError(
        f"Cannot extract text from PDF: {pdf_path}. "
        "Install pdfplumber (`pip install pdfplumber`) or PyPDF2 (`pip install PyPDF2`)."
    )


def _extract_text_from_docx(docx_path: str) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        import docx
        doc = docx.Document(docx_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except ImportError:
        raise RuntimeError(
            f"Cannot extract text from DOCX: {docx_path}. "
            "Install python-docx (`pip install python-docx`)."
        )


def parse_resume(file_path: str) -> ResumeData:
    """
    Parse a resume file (PDF or DOCX) into structured data.
    Uses AI to extract structured information from raw text.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        raw_text = _extract_text_from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        raw_text = _extract_text_from_docx(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    else:
        raise ValueError(f"Unsupported resume format: {ext}. Use PDF, DOCX, or TXT.")

    print(f"[profile] Resume extracted — {len(raw_text)} chars from {file_path}")

    # Use AI to structure the resume
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": """You are a resume parser. Extract structured data from the resume text.
Return ONLY valid JSON:
{
  "skills": ["skill1", "skill2", ...],
  "experience_summary": "<concise summary of work experience>",
  "education": "<education details>",
  "projects": ["project1 description", "project2 description", ...],
  "certifications": ["cert1", "cert2", ...],
  "total_years_experience": <float or null>
}"""},
            {"role": "user", "content": f"RESUME TEXT:\n{raw_text[:8000]}"},
        ],
        temperature=0.1,
        max_tokens=1500,
        response_format={"type": "json_object"},
    )

    try:
        data = json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        data = {}

    print(f"[profile] Resume parsed — {len(data.get('skills', []))} skills found")

    return ResumeData(
        raw_text=raw_text,
        skills=data.get("skills", []),
        experience_summary=data.get("experience_summary", ""),
        education=data.get("education", ""),
        projects=data.get("projects", []),
        certifications=data.get("certifications", []),
        total_years_experience=data.get("total_years_experience"),
    )


# ── GitHub Profile Parsing ────────────────────────────────────────────────────

def _normalize_github_url(github_input: str) -> str:
    """Convert GitHub input (URL or username) to profile URL."""
    github_input = github_input.strip().rstrip("/")
    if github_input.startswith("http"):
        return github_input
    # Assume it's a username
    return f"https://github.com/{github_input}"


def _fetch_github_api(username: str) -> Dict:
    """Fetch GitHub data via public API (no auth needed for basic info)."""
    import urllib.request
    import urllib.error

    data = {"profile": {}, "repos": []}

    # Fetch profile
    try:
        req = urllib.request.Request(
            f"https://api.github.com/users/{username}",
            headers={"User-Agent": "InterviewAnalyzer/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data["profile"] = json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"[profile] ⚠ GitHub profile fetch failed: {e}")
        return data

    # Fetch repos (top 30 by most recently updated)
    try:
        req = urllib.request.Request(
            f"https://api.github.com/users/{username}/repos?sort=updated&per_page=30",
            headers={"User-Agent": "InterviewAnalyzer/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data["repos"] = json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"[profile] ⚠ GitHub repos fetch failed: {e}")

    return data


def parse_github(github_input: str) -> GitHubData:
    """
    Parse GitHub profile from URL or username.
    Uses GitHub public API for structured data.
    """
    profile_url = _normalize_github_url(github_input)

    # Extract username from URL
    parts = profile_url.rstrip("/").split("/")
    username = parts[-1] if parts else github_input

    print(f"[profile] Fetching GitHub profile: {username}")

    api_data = _fetch_github_api(username)
    profile = api_data.get("profile", {})
    repos_raw = api_data.get("repos", [])

    # Process repos
    repos = []
    languages = {}
    for r in repos_raw:
        if isinstance(r, dict) and not r.get("fork", False):
            lang = r.get("language", "")
            repos.append({
                "name": r.get("name", ""),
                "description": r.get("description", "") or "",
                "language": lang or "Unknown",
                "stars": r.get("stargazers_count", 0),
            })
            if lang:
                languages[lang] = languages.get(lang, 0) + 1

    top_languages = sorted(languages, key=languages.get, reverse=True)[:8]

    # Build text summary for AI analysis
    bio = profile.get("bio", "") or ""
    raw_parts = [
        f"GitHub Username: {username}",
        f"Bio: {bio}",
        f"Public Repos: {profile.get('public_repos', 0)}",
        f"Followers: {profile.get('followers', 0)}",
        f"Top Languages: {', '.join(top_languages)}",
        "\nRepositories:",
    ]
    for r in repos[:15]:
        raw_parts.append(f"  - {r['name']} ({r['language']}): {r['description']}")

    raw_text = "\n".join(raw_parts)

    contribution = (
        f"{username} has {profile.get('public_repos', 0)} public repos, "
        f"{profile.get('followers', 0)} followers. "
        f"Primary languages: {', '.join(top_languages[:5])}."
    )

    print(f"[profile] GitHub parsed — {len(repos)} repos, languages: {', '.join(top_languages[:5])}")

    return GitHubData(
        username=username,
        profile_url=profile_url,
        bio=bio,
        repos=repos,
        top_languages=top_languages,
        total_repos=len(repos),
        contribution_summary=contribution,
        raw_text=raw_text,
    )


# ── LinkedIn Profile Parsing ─────────────────────────────────────────────────

def _normalize_linkedin_url(linkedin_input: str) -> str:
    """Convert LinkedIn input (URL or ID) to profile URL."""
    linkedin_input = linkedin_input.strip().rstrip("/")
    if linkedin_input.startswith("http"):
        return linkedin_input
    return f"https://www.linkedin.com/in/{linkedin_input}"


def parse_linkedin(linkedin_input: str, raw_text: str = None) -> LinkedInData:
    """
    Parse LinkedIn profile. Since LinkedIn blocks scraping, this accepts
    either a pre-scraped text dump or uses the URL as reference.

    In production, integrate with:
      - LinkedIn API (requires OAuth)
      - Proxycurl API
      - User-provided LinkedIn PDF export

    Args:
        linkedin_input: URL or username/ID
        raw_text: Optional pre-scraped or user-provided LinkedIn text
    """
    profile_url = _normalize_linkedin_url(linkedin_input)

    if raw_text:
        # Parse provided text with AI
        client = Groq(api_key=os.environ["GROQ_API_KEY"])

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": """Parse this LinkedIn profile text. Return ONLY valid JSON:
{
  "headline": "<professional headline>",
  "summary": "<about section>",
  "experience": [{"title": "", "company": "", "duration": "", "description": ""}],
  "skills": ["skill1", "skill2"],
  "education": [{"institution": "", "degree": "", "field": ""}]
}"""},
                {"role": "user", "content": f"LINKEDIN PROFILE:\n{raw_text[:6000]}"},
            ],
            temperature=0.1,
            max_tokens=1500,
            response_format={"type": "json_object"},
        )

        try:
            data = json.loads(response.choices[0].message.content.strip())
        except json.JSONDecodeError:
            data = {}

        print(f"[profile] LinkedIn parsed — {len(data.get('skills', []))} skills found")

        return LinkedInData(
            profile_url=profile_url,
            headline=data.get("headline", ""),
            summary=data.get("summary", ""),
            experience=data.get("experience", []),
            skills=data.get("skills", []),
            education=data.get("education", []),
            raw_text=raw_text,
        )

    # If no text provided, create a placeholder with just the URL
    print(f"[profile] LinkedIn URL recorded: {profile_url} (no text provided for deep parsing)")
    return LinkedInData(
        profile_url=profile_url,
        headline="",
        summary="",
        experience=[],
        skills=[],
        education=[],
        raw_text=f"LinkedIn Profile URL: {profile_url}",
    )


# ── Profile Synthesis ─────────────────────────────────────────────────────────

def synthesize_profile(
    resume: Optional[ResumeData] = None,
    github: Optional[GitHubData] = None,
    linkedin: Optional[LinkedInData] = None,
) -> CandidateProfile:
    """
    Merge data from all profile sources into a unified CandidateProfile.
    Uses AI to detect discrepancies and generate a unified summary.
    """
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    # Collect all claimed skills
    all_skills = set()
    profile_texts = []

    if resume:
        all_skills.update(resume.skills)
        profile_texts.append(f"RESUME:\n{resume.raw_text[:4000]}")

    if github:
        all_skills.update(github.top_languages)
        profile_texts.append(f"GITHUB:\n{github.raw_text[:3000]}")

    if linkedin:
        all_skills.update(linkedin.skills)
        profile_texts.append(f"LINKEDIN:\n{linkedin.raw_text[:3000]}")

    combined_text = "\n\n---\n\n".join(profile_texts)

    if not combined_text:
        return CandidateProfile(
            resume=resume,
            github=github,
            linkedin=linkedin,
            synthesized_summary="No profile data provided.",
            claimed_skills=[],
            claimed_experience="",
            verification_notes=["No profile data available for verification."],
        )

    # AI synthesis
    print("[profile] Synthesizing unified candidate profile...")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": """You are a candidate profile analyst.
Analyze the provided profile data from multiple sources (resume, GitHub, LinkedIn).
Create a unified summary and identify any discrepancies.

Return ONLY valid JSON:
{
  "synthesized_summary": "<unified 3-4 sentence summary of the candidate>",
  "claimed_experience": "<concise narrative of their work experience>",
  "verification_notes": [
    "<any discrepancy or notable point between sources>",
    "<skill claimed but not evidenced>",
    "<experience inconsistency>"
  ]
}"""},
            {"role": "user", "content": combined_text},
        ],
        temperature=0.2,
        max_tokens=1000,
        response_format={"type": "json_object"},
    )

    try:
        data = json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        data = {}

    print(f"[profile] Profile synthesized — {len(all_skills)} total skills across sources")

    return CandidateProfile(
        resume=resume,
        github=github,
        linkedin=linkedin,
        synthesized_summary=data.get("synthesized_summary", "Profile analysis complete."),
        claimed_skills=sorted(list(all_skills)),
        claimed_experience=data.get("claimed_experience", ""),
        verification_notes=data.get("verification_notes", []),
    )
