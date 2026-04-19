"""
pipeline_v2.py
Full Interview Evaluation Pipeline — v2

Two-phase flow (both phases run on Groq's free tier):

  Step 1 — TRANSCRIPTION (Groq Whisper)
      transcribe() in transcriber.py calls `whisper-large-v3` to turn the
      uploaded audio/video into text with word-level timestamps.

  Step 2 — ANALYSIS (Groq Llama)
      diarize() + score_interview() call `llama-3.3-70b-versatile` to split
      interviewer vs candidate speech, then score the interview on a 100-point
      rubric and emit structured insights (strengths, improvements, summary).

Pipeline steps in detail:
  1. Parse candidate profile (resume, GitHub, LinkedIn)
  2. [Step 1] Transcribe interview audio/video via Groq Whisper
  3. [Step 2] Diarize speakers via Groq Llama
  4. Run rule engine on candidate-only speech (pure Python)
  5. [Step 2] Score interview via Groq Llama using 30/40/20/10 rubric
  6. Generate structured report out of 100

Usage:
    from pipeline_v2 import evaluate_interview

    report = evaluate_interview(
        interview_path="interview.mp3",
        job_description="Software Engineer at Google...",
        resume_path="resume.pdf",
        github_url="https://github.com/johndoe",
        linkedin_url="https://linkedin.com/in/johndoe",
    )
    report.print_report()
    print(report.to_json())
"""

import os
import json
import time
from dotenv import load_dotenv
from typing import Optional

load_dotenv()  # loads GROQ_API_KEY from .env

from transcriber import transcribe
from speaker_diarizer import diarize, DiarizationResult, _parse_json_transcript
from rule_engine import analyze as rule_analyze
from evaluator import evaluate as eval_quality
from profile_parser import (
    parse_resume,
    parse_github,
    parse_linkedin,
    synthesize_profile,
    CandidateProfile,
)
from interview_scorer import score_interview, ScoringReport


def _load_transcript_from_json(json_path: str) -> str:
    """Load a transcript from a JSON file."""
    with open(json_path, "r", encoding="utf-8") as f:
        content = f.read()
    return _parse_json_transcript(content)


def evaluate_interview(
    # ── Session data (per evaluation) ─────────────────────────────────
    interview_path: str,                     # audio/video/transcript file
    job_description: str = "",               # JD with title, role, company
    job_title: str = "",                     # optional separate job title
    company_name: str = "",                  # optional company name

    # ── Profile data (from signup/profile) ────────────────────────────
    resume_path: Optional[str] = None,       # path to PDF/DOCX resume
    github_url: Optional[str] = None,        # GitHub profile URL or username
    linkedin_url: Optional[str] = None,      # LinkedIn profile URL or ID
    linkedin_text: Optional[str] = None,     # pre-scraped LinkedIn text

    # ── Options ───────────────────────────────────────────────────────
    language: str = "en",
    transcript_text: Optional[str] = None,   # pre-provided transcript text
) -> ScoringReport:
    """
    Full interview evaluation pipeline.

    Args:
        interview_path  : path to MP3/MP4/WAV or JSON transcript file
        job_description : full job posting text
        job_title       : job title (appended to JD if separate)
        company_name    : company name (appended to JD if separate)
        resume_path     : path to candidate's resume (PDF/DOCX)
        github_url      : GitHub profile URL or username
        linkedin_url    : LinkedIn profile URL or ID
        linkedin_text   : pre-scraped LinkedIn profile text
        language        : transcript language code
        transcript_text : pre-provided transcript text (skips transcription)

    Returns:
        ScoringReport with full 100-point breakdown
    """
    if not os.environ.get("GROQ_API_KEY"):
        raise EnvironmentError("GROQ_API_KEY not set. Add it to .env file.")

    start = time.time()

    # Build full JD
    full_jd = job_description
    if job_title and job_title not in full_jd:
        full_jd = f"Job Title: {job_title}\n{full_jd}"
    if company_name and company_name not in full_jd:
        full_jd = f"Company: {company_name}\n{full_jd}"

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 1: Parse Candidate Profile
    # ══════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 60)
    print("  STEP 1/5 — PARSING CANDIDATE PROFILE")
    print("═" * 60)

    resume_data = None
    github_data = None
    linkedin_data = None

    if resume_path and os.path.exists(resume_path):
        try:
            resume_data = parse_resume(resume_path)
            print(f"  ✅ Resume parsed: {len(resume_data.skills)} skills extracted")
        except Exception as e:
            print(f"  ⚠ Resume parsing failed: {e}")

    if github_url:
        try:
            github_data = parse_github(github_url)
            print(f"  ✅ GitHub parsed: {github_data.total_repos} repos, "
                  f"languages: {', '.join(github_data.top_languages[:4])}")
        except Exception as e:
            print(f"  ⚠ GitHub parsing failed: {e}")

    if linkedin_url:
        try:
            linkedin_data = parse_linkedin(linkedin_url, raw_text=linkedin_text)
            print(f"  ✅ LinkedIn recorded: {linkedin_data.profile_url}")
        except Exception as e:
            print(f"  ⚠ LinkedIn parsing failed: {e}")

    # Synthesize profile
    profile = None
    if resume_data or github_data or linkedin_data:
        profile = synthesize_profile(resume_data, github_data, linkedin_data)
        print(f"  ✅ Profile synthesized: {len(profile.claimed_skills)} total skills")
    else:
        print("  ⚠ No profile data provided — consistency scoring will use defaults")

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 2: Transcribe Interview
    # ══════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 60)
    print("  STEP 2/5 — TRANSCRIBING INTERVIEW")
    print("═" * 60)

    raw_transcript = ""
    word_timestamps = []
    duration_seconds = 0.0

    ext = os.path.splitext(interview_path)[1].lower() if interview_path else ""

    if transcript_text:
        # Pre-provided transcript
        raw_transcript = transcript_text
        print(f"  ✅ Using pre-provided transcript ({len(raw_transcript)} chars)")

    elif ext == ".json":
        # JSON transcript file
        raw_transcript = _load_transcript_from_json(interview_path)
        print(f"  ✅ Loaded JSON transcript ({len(raw_transcript)} chars)")

    elif ext in (".mp3", ".mp4", ".wav", ".m4a", ".webm", ".ogg"):
        # Audio/video file — transcribe
        if not os.path.exists(interview_path):
            raise FileNotFoundError(f"Interview file not found: {interview_path}")

        transcript_result = transcribe(interview_path, language=language)
        raw_transcript = transcript_result.text
        word_timestamps = transcript_result.word_timestamps
        duration_seconds = transcript_result.duration_seconds
        print(f"  ✅ Transcribed: {len(raw_transcript.split())} words, "
              f"{duration_seconds:.1f}s duration")
    else:
        # Try reading as plain text
        if os.path.exists(interview_path):
            with open(interview_path, "r", encoding="utf-8") as f:
                raw_transcript = f.read()
            print(f"  ✅ Loaded text transcript ({len(raw_transcript)} chars)")
        else:
            raise ValueError(
                f"Unsupported file format or file not found: {interview_path}. "
                "Supported: MP3, MP4, WAV, M4A, WEBM, OGG, JSON, TXT"
            )

    if not raw_transcript.strip():
        raise ValueError("Empty transcript — cannot evaluate.")

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 3: Speaker Diarization
    # ══════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 60)
    print("  STEP 3/5 — IDENTIFYING SPEAKERS")
    print("═" * 60)

    diarization = diarize(
        transcript=raw_transcript,
        job_description=full_jd,
        word_timestamps=word_timestamps,
    )

    print(f"  ✅ Diarization complete:")
    print(f"     Candidate: {diarization.candidate_word_count} words")
    print(f"     Interviewer: {diarization.interviewer_word_count} words")
    print(f"     Questions detected: {len(diarization.questions_detected)}")
    print(f"     Ambiguous turns: {diarization.ambiguous_turns}")

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 4: Rule Engine Analysis (candidate speech only)
    # ══════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 60)
    print("  STEP 4/5 — ANALYZING COMMUNICATION METRICS")
    print("═" * 60)

    # Run rule engine on CANDIDATE speech only
    rule = rule_analyze(
        transcript=diarization.candidate_text,
        word_timestamps=word_timestamps,  # Note: timestamps are from full audio
        duration_seconds=duration_seconds if duration_seconds > 0 else None,
    )

    # Also get tone/quality from the evaluator (on candidate speech only)
    ev = eval_quality(
        transcript=diarization.candidate_text,
        question="\n".join(diarization.questions_detected[:5]) if diarization.questions_detected else None,
    )

    print(f"  ✅ Communication metrics:")
    print(f"     WPM: {rule.wpm} ({rule.speed_label})")
    print(f"     Fillers: {rule.filler_count} ({rule.filler_rate_per_min}/min)")
    print(f"     Tone: {ev.tone}")

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 5: Score Interview (30/40/20/10 rubric)
    # ══════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 60)
    print("  STEP 5/5 — SCORING (100-POINT RUBRIC)")
    print("═" * 60)

    report = score_interview(
        diarization=diarization,
        rule=rule,
        job_description=full_jd,
        profile=profile,
        tone=ev.tone,
    )

    elapsed = round(time.time() - start, 2)
    print(f"\n⏱  Total processing time: {elapsed:.1f}s")

    return report


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="AI Interview Evaluator — Score interview performance out of 100",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic evaluation (audio only)
  python pipeline_v2.py interview.mp3

  # Full evaluation with all inputs
  python pipeline_v2.py interview.mp3 \\
    --jd "Software Engineer at Google. Requirements: Python, ML, 3+ years..." \\
    --resume resume.pdf \\
    --github johndoe \\
    --linkedin johndoe

  # Evaluate a JSON transcript
  python pipeline_v2.py transcript.json --jd "Data Scientist role..."
        """
    )

    parser.add_argument("interview", help="Path to interview file (MP3, MP4, WAV, JSON, TXT)")
    parser.add_argument("--jd", default="", help="Job description text")
    parser.add_argument("--job-title", default="", help="Job title")
    parser.add_argument("--company", default="", help="Company name")
    parser.add_argument("--resume", default=None, help="Path to resume (PDF/DOCX)")
    parser.add_argument("--github", default=None, help="GitHub URL or username")
    parser.add_argument("--linkedin", default=None, help="LinkedIn URL or ID")
    parser.add_argument("--language", default="en", help="Transcript language (default: en)")
    parser.add_argument("--json-output", default=None, help="Save JSON report to file")

    args = parser.parse_args()

    report = evaluate_interview(
        interview_path=args.interview,
        job_description=args.jd,
        job_title=args.job_title,
        company_name=args.company,
        resume_path=args.resume,
        github_url=args.github,
        linkedin_url=args.linkedin,
        language=args.language,
    )

    # Print the report
    report.print_report()

    # Save JSON if requested
    output_path = args.json_output
    if not output_path:
        base = args.interview.rsplit(".", 1)[0]
        output_path = f"{base}_evaluation.json"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report.to_json())
    print(f"[pipeline] JSON report saved → {output_path}")
