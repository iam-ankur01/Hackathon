"""
interview_scorer.py
Structured 100-point scoring rubric for interview evaluation.

Rubric Breakdown:
  30 pts — Public Speaking (clarity, tone, confidence, articulation)
  40 pts — Answer Correctness & Relevance (vs questions + job description)
  20 pts — Consistency & Truthfulness (cross-verified against resume/GitHub/LinkedIn)
  10 pts — Filler Word Assessment (candidate-only analysis)

Total: 100 points
"""

import os
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from groq import Groq

from speaker_diarizer import DiarizationResult
from profile_parser import CandidateProfile
from rule_engine import RuleAnalysis


@dataclass
class CategoryScore:
    category: str
    max_points: int
    scored_points: float
    justification: str
    sub_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class ScoringReport:
    # ── Category Scores ───────────────────────────────────────────────
    public_speaking: CategoryScore       # 30 pts
    answer_quality: CategoryScore        # 40 pts
    consistency: CategoryScore           # 20 pts
    filler_assessment: CategoryScore     # 10 pts

    # ── Total ─────────────────────────────────────────────────────────
    total_score: float                   # out of 100
    grade: str

    # ── Qualitative ───────────────────────────────────────────────────
    strengths: List[str]
    areas_for_improvement: List[str]
    executive_summary: str

    # ── Metadata ──────────────────────────────────────────────────────
    questions_evaluated: List[str]
    candidate_word_count: int
    interviewer_word_count: int
    diarization_confidence: float

    def to_dict(self) -> dict:
        return {
            "total_score": round(self.total_score, 1),
            "grade": self.grade,
            "category_breakdown": {
                "public_speaking": {
                    "score": round(self.public_speaking.scored_points, 1),
                    "max": self.public_speaking.max_points,
                    "justification": self.public_speaking.justification,
                    "sub_scores": self.public_speaking.sub_scores,
                },
                "answer_quality": {
                    "score": round(self.answer_quality.scored_points, 1),
                    "max": self.answer_quality.max_points,
                    "justification": self.answer_quality.justification,
                    "sub_scores": self.answer_quality.sub_scores,
                },
                "consistency_truthfulness": {
                    "score": round(self.consistency.scored_points, 1),
                    "max": self.consistency.max_points,
                    "justification": self.consistency.justification,
                    "sub_scores": self.consistency.sub_scores,
                },
                "filler_word_assessment": {
                    "score": round(self.filler_assessment.scored_points, 1),
                    "max": self.filler_assessment.max_points,
                    "justification": self.filler_assessment.justification,
                    "sub_scores": self.filler_assessment.sub_scores,
                },
            },
            "strengths": self.strengths,
            "areas_for_improvement": self.areas_for_improvement,
            "executive_summary": self.executive_summary,
            "metadata": {
                "questions_evaluated": self.questions_evaluated,
                "candidate_word_count": self.candidate_word_count,
                "interviewer_word_count": self.interviewer_word_count,
                "diarization_confidence": round(self.diarization_confidence, 2),
            }
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def print_report(self):
        """Pretty-print the full scoring report."""
        print(f"\n{'═' * 70}")
        print(f"  INTERVIEW PERFORMANCE REPORT")
        print(f"{'═' * 70}")

        # Total score bar
        bar_len = 40
        filled = int(self.total_score / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"\n  TOTAL SCORE: {self.total_score:.1f} / 100    Grade: {self.grade}")
        print(f"  [{bar}]\n")

        divider = "─" * 70

        # Category breakdown
        categories = [
            ("🎤 PUBLIC SPEAKING", self.public_speaking),
            ("✅ ANSWER QUALITY & RELEVANCE", self.answer_quality),
            ("🔍 CONSISTENCY & TRUTHFULNESS", self.consistency),
            ("🗣️  FILLER WORD ASSESSMENT", self.filler_assessment),
        ]

        for title, cat in categories:
            print(f"{divider}")
            pct = cat.scored_points / cat.max_points * 100 if cat.max_points else 0
            filled = int(pct / 100 * 20)
            bar = "█" * filled + "░" * (20 - filled)
            print(f"  {title}")
            print(f"  Score: {cat.scored_points:.1f} / {cat.max_points}  [{bar}]")
            print(f"  {cat.justification}")

            if cat.sub_scores:
                for sub_name, sub_val in cat.sub_scores.items():
                    print(f"    • {sub_name}: {sub_val}")
            print()

        # Strengths
        if self.strengths:
            print(f"{divider}")
            print(f"  ✅ STRENGTHS")
            for s in self.strengths:
                print(f"    • {s}")

        # Areas for improvement
        if self.areas_for_improvement:
            print(f"\n{divider}")
            print(f"  ⚠️  AREAS FOR IMPROVEMENT")
            for a in self.areas_for_improvement:
                print(f"    • {a}")

        # Executive summary
        print(f"\n{divider}")
        print(f"  📋 EXECUTIVE SUMMARY")
        print(f"  {self.executive_summary}")

        print(f"\n{'═' * 70}\n")


# ── Score computation helpers ─────────────────────────────────────────────────

def _score_to_grade(score: float) -> str:
    if score >= 95: return "A+"
    if score >= 90: return "A"
    if score >= 85: return "A-"
    if score >= 80: return "B+"
    if score >= 75: return "B"
    if score >= 70: return "B-"
    if score >= 65: return "C+"
    if score >= 60: return "C"
    if score >= 55: return "C-"
    if score >= 50: return "D+"
    if score >= 45: return "D"
    if score >= 40: return "D-"
    return "F"


# ── Category 1: Public Speaking (30 pts) ──────────────────────────────────────

PUBLIC_SPEAKING_PROMPT = """You are an expert public speaking coach evaluating an interview candidate.
Analyze ONLY the CANDIDATE's speech (not the interviewer's) and score these dimensions:

1. Clarity (0-8): Is the speech clear, well-articulated, and easy to understand?
   - Clear sentence structure, logical flow, no rambling
2. Tone (0-8): Is the tone professional, confident, and appropriate?
   - Not monotone, not overly casual, good energy
3. Confidence (0-8): Does the candidate speak with conviction?
   - No excessive hedging, owns their statements, assertive
4. Articulation (0-6): Is the pacing good? Are words well-pronounced?
   - Good WPM range (120-160), no mumbling, clear enunciation

Total maximum: 30 points

Context:
- WPM: {wpm} ({speed_label})
- Filler rate: {filler_rate}/min
- Tone detected: {tone}

Return ONLY valid JSON:
{{
  "clarity_score": <int 0-8>,
  "tone_score": <int 0-8>,
  "confidence_score": <int 0-8>,
  "articulation_score": <int 0-6>,
  "total": <int 0-30>,
  "justification": "<2-3 sentences explaining the scores>"
}}"""


def _score_public_speaking(
    candidate_text: str,
    rule: RuleAnalysis,
    tone: str,
) -> CategoryScore:
    """Score public speaking: clarity, tone, confidence, articulation (30 pts)."""
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    prompt = PUBLIC_SPEAKING_PROMPT.format(
        wpm=rule.wpm,
        speed_label=rule.speed_label,
        filler_rate=rule.filler_rate_per_min,
        tone=tone,
    )

    print("[scorer] Evaluating public speaking (30 pts)...")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"CANDIDATE'S SPEECH:\n{candidate_text[:8000]}"},
        ],
        temperature=0.15,
        max_tokens=600,
        response_format={"type": "json_object"},
    )

    try:
        data = json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        data = {"clarity_score": 4, "tone_score": 4, "confidence_score": 4,
                "articulation_score": 3, "total": 15, "justification": "Default scoring applied."}

    total = min(30, data.get("total", 15))

    return CategoryScore(
        category="Public Speaking",
        max_points=30,
        scored_points=total,
        justification=data.get("justification", ""),
        sub_scores={
            "Clarity (0-8)": data.get("clarity_score", 4),
            "Tone (0-8)": data.get("tone_score", 4),
            "Confidence (0-8)": data.get("confidence_score", 4),
            "Articulation (0-6)": data.get("articulation_score", 3),
        }
    )


# ── Category 2: Answer Correctness & Relevance (40 pts) ──────────────────────

ANSWER_QUALITY_PROMPT = """You are a senior technical interviewer evaluating a candidate's answers.
Score the CANDIDATE's responses based on correctness and relevance.

You have:
1. The interview questions asked by the interviewer
2. The candidate's answers
3. The job description for context

Score these dimensions:
1. Technical Correctness (0-15): Are the answers factually correct?
   - Accurate technical statements, correct methodologies, valid approaches
2. Relevance to Questions (0-13): Do answers directly address what was asked?
   - On-topic, no tangential rambling, addresses the core question
3. Relevance to Job Description (0-12): Do answers demonstrate fitness for the role?
   - Relevant experience highlighted, appropriate skill demonstration

Total maximum: 40 points

Return ONLY valid JSON:
{{
  "correctness_score": <int 0-15>,
  "question_relevance_score": <int 0-13>,
  "jd_relevance_score": <int 0-12>,
  "total": <int 0-40>,
  "justification": "<2-3 sentences explaining the scores>"
}}"""


def _score_answer_quality(
    candidate_text: str,
    questions: List[str],
    job_description: str,
) -> CategoryScore:
    """Score answer correctness and relevance (40 pts)."""
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    user_content = ""
    if job_description:
        user_content += f"JOB DESCRIPTION:\n{job_description[:3000]}\n\n"
    if questions:
        user_content += f"INTERVIEW QUESTIONS:\n" + "\n".join(f"Q{i+1}: {q}" for i, q in enumerate(questions)) + "\n\n"
    user_content += f"CANDIDATE'S ANSWERS:\n{candidate_text[:8000]}"

    print("[scorer] Evaluating answer quality & relevance (40 pts)...")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": ANSWER_QUALITY_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.15,
        max_tokens=600,
        response_format={"type": "json_object"},
    )

    try:
        data = json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        data = {"correctness_score": 8, "question_relevance_score": 7,
                "jd_relevance_score": 5, "total": 20, "justification": "Default scoring applied."}

    total = min(40, data.get("total", 20))

    return CategoryScore(
        category="Answer Quality & Relevance",
        max_points=40,
        scored_points=total,
        justification=data.get("justification", ""),
        sub_scores={
            "Technical Correctness (0-15)": data.get("correctness_score", 8),
            "Question Relevance (0-13)": data.get("question_relevance_score", 7),
            "JD Relevance (0-12)": data.get("jd_relevance_score", 5),
        }
    )


# ── Category 3: Consistency & Truthfulness (20 pts) ──────────────────────────

CONSISTENCY_PROMPT = """You are a candidate verification specialist.
Cross-reference the candidate's interview answers against their profile data.

Score these dimensions:
1. Resume Consistency (0-8): Do claims in the interview match the resume?
   - Job titles, company names, project descriptions, timelines
2. GitHub Verification (0-6): Does the candidate's technical depth match their GitHub?
   - Languages they claim vs. what's on GitHub, project descriptions
3. LinkedIn Consistency (0-6): Do career claims match LinkedIn?
   - Experience timeline, role descriptions, skills endorsements

If a profile source is not available, score proportionally based on available data.

Total maximum: 20 points

Return ONLY valid JSON:
{{
  "resume_consistency_score": <int 0-8>,
  "github_verification_score": <int 0-6>,
  "linkedin_consistency_score": <int 0-6>,
  "total": <int 0-20>,
  "justification": "<2-3 sentences explaining findings>",
  "discrepancies": ["<specific discrepancy 1>", "<specific discrepancy 2>"]
}}"""


def _score_consistency(
    candidate_text: str,
    profile: Optional[CandidateProfile],
) -> CategoryScore:
    """Score consistency and truthfulness against profile data (20 pts)."""

    if not profile or (not profile.resume and not profile.github and not profile.linkedin):
        return CategoryScore(
            category="Consistency & Truthfulness",
            max_points=20,
            scored_points=14.0,  # Default neutral score when no profile data
            justification="No profile data provided for cross-verification. Default score applied.",
            sub_scores={
                "Resume Consistency (0-8)": "N/A",
                "GitHub Verification (0-6)": "N/A",
                "LinkedIn Consistency (0-6)": "N/A",
            }
        )

    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    profile_context = f"CANDIDATE PROFILE SUMMARY:\n{profile.synthesized_summary}\n\n"

    if profile.resume:
        profile_context += f"RESUME EXCERPT:\n{profile.resume.raw_text[:3000]}\n\n"
    if profile.github:
        profile_context += f"GITHUB PROFILE:\n{profile.github.raw_text[:2000]}\n\n"
    if profile.linkedin:
        profile_context += f"LINKEDIN PROFILE:\n{profile.linkedin.raw_text[:2000]}\n\n"

    if profile.verification_notes:
        profile_context += f"PRE-IDENTIFIED NOTES:\n" + "\n".join(f"- {n}" for n in profile.verification_notes)

    user_content = profile_context + f"\n\nCANDIDATE'S INTERVIEW ANSWERS:\n{candidate_text[:6000]}"

    print("[scorer] Evaluating consistency & truthfulness (20 pts)...")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": CONSISTENCY_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.15,
        max_tokens=700,
        response_format={"type": "json_object"},
    )

    try:
        data = json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        data = {"resume_consistency_score": 5, "github_verification_score": 3,
                "linkedin_consistency_score": 3, "total": 11, "justification": "Default scoring applied."}

    total = min(20, data.get("total", 11))

    sub_scores = {}
    if profile.resume:
        sub_scores["Resume Consistency (0-8)"] = data.get("resume_consistency_score", 5)
    else:
        sub_scores["Resume Consistency (0-8)"] = "N/A (not provided)"
    if profile.github:
        sub_scores["GitHub Verification (0-6)"] = data.get("github_verification_score", 3)
    else:
        sub_scores["GitHub Verification (0-6)"] = "N/A (not provided)"
    if profile.linkedin:
        sub_scores["LinkedIn Consistency (0-6)"] = data.get("linkedin_consistency_score", 3)
    else:
        sub_scores["LinkedIn Consistency (0-6)"] = "N/A (not provided)"

    discrepancies = data.get("discrepancies", [])
    justification = data.get("justification", "")
    if discrepancies:
        justification += " Discrepancies: " + "; ".join(discrepancies[:3])

    return CategoryScore(
        category="Consistency & Truthfulness",
        max_points=20,
        scored_points=total,
        justification=justification,
        sub_scores=sub_scores,
    )


# ── Category 4: Filler Word Assessment (10 pts) ──────────────────────────────

def _score_filler_words(rule: RuleAnalysis) -> CategoryScore:
    """
    Score filler word usage from the candidate's speech (10 pts).
    Pure rule-based scoring — no API call needed.

    Scoring:
      - 0-1 fillers/min → 10 pts (excellent)
      - 1-2 fillers/min → 9 pts
      - 2-3 fillers/min → 8 pts
      - 3-4 fillers/min → 7 pts
      - 4-5 fillers/min → 6 pts
      - 5-7 fillers/min → 5 pts
      - 7-9 fillers/min → 4 pts
      - 9-12 fillers/min → 3 pts
      - 12-15 fillers/min → 2 pts
      - 15+ fillers/min → 1 pt
    """
    rate = rule.filler_rate_per_min

    if rate <= 1:
        score = 10.0
    elif rate <= 2:
        score = 9.0
    elif rate <= 3:
        score = 8.0
    elif rate <= 4:
        score = 7.0
    elif rate <= 5:
        score = 6.0
    elif rate <= 7:
        score = 5.0
    elif rate <= 9:
        score = 4.0
    elif rate <= 12:
        score = 3.0
    elif rate <= 15:
        score = 2.0
    else:
        score = 1.0

    # Build filler word breakdown
    filler_counts = {}
    for hit in rule.filler_hits:
        w = hit.word.lower()
        filler_counts[w] = filler_counts.get(w, 0) + 1

    top_fillers = sorted(filler_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    filler_breakdown = {f'"{w}"': count for w, count in top_fillers}

    justification = (
        f"Candidate used {rule.filler_count} filler words "
        f"({rule.filler_rate_per_min}/min, {rule.filler_percentage}% of total words). "
    )
    if rate <= 2:
        justification += "Excellent control — minimal filler usage."
    elif rate <= 5:
        justification += "Acceptable but could reduce filler frequency for stronger delivery."
    elif rate <= 9:
        justification += "Noticeable filler usage that detracts from credibility. Practice pausing instead."
    else:
        justification += "Excessive filler words significantly impact perceived competence. Urgent improvement needed."

    return CategoryScore(
        category="Filler Word Assessment",
        max_points=10,
        scored_points=score,
        justification=justification,
        sub_scores={
            "Filler Rate (per min)": rule.filler_rate_per_min,
            "Total Filler Count": rule.filler_count,
            "Filler % of Speech": rule.filler_percentage,
            **filler_breakdown,
        }
    )


# ── Master Scoring Function ──────────────────────────────────────────────────

def score_interview(
    diarization: DiarizationResult,
    rule: RuleAnalysis,
    job_description: str = "",
    profile: Optional[CandidateProfile] = None,
    tone: str = "neutral",
) -> ScoringReport:
    """
    Generate the complete 100-point scoring report.

    Args:
        diarization    : speaker-separated transcript
        rule           : filler/pause/WPM analysis (on candidate speech)
        job_description: the job posting / role description
        profile        : candidate's resume + GitHub + LinkedIn
        tone           : detected vocal tone

    Returns:
        ScoringReport with full breakdown
    """
    candidate_text = diarization.candidate_text
    questions = diarization.questions_detected

    # Avg confidence of diarization
    if diarization.turns:
        diar_confidence = sum(t.confidence for t in diarization.turns) / len(diarization.turns)
    else:
        diar_confidence = 0.5

    # ── Score each category ───────────────────────────────────────────────────
    ps_score = _score_public_speaking(candidate_text, rule, tone)
    aq_score = _score_answer_quality(candidate_text, questions, job_description)
    cs_score = _score_consistency(candidate_text, profile)
    fw_score = _score_filler_words(rule)

    # ── Total ─────────────────────────────────────────────────────────────────
    total = (
        ps_score.scored_points +
        aq_score.scored_points +
        cs_score.scored_points +
        fw_score.scored_points
    )
    total = round(min(100.0, max(0.0, total)), 1)
    grade = _score_to_grade(total)

    # ── Generate strengths & improvements via AI ──────────────────────────────
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    summary_context = f"""
Score Breakdown:
- Public Speaking: {ps_score.scored_points}/{ps_score.max_points} — {ps_score.justification}
- Answer Quality: {aq_score.scored_points}/{aq_score.max_points} — {aq_score.justification}
- Consistency: {cs_score.scored_points}/{cs_score.max_points} — {cs_score.justification}
- Filler Words: {fw_score.scored_points}/{fw_score.max_points} — {fw_score.justification}
- TOTAL: {total}/100 (Grade: {grade})

Candidate's speech excerpt:
{candidate_text[:3000]}
"""

    print("[scorer] Generating final summary...")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": """Based on the interview score breakdown, provide:
1. Top 3-5 specific strengths
2. Top 3-5 specific areas for improvement  
3. A 3-sentence executive summary

Return ONLY valid JSON:
{
  "strengths": ["<strength 1>", "<strength 2>", ...],
  "areas_for_improvement": ["<area 1>", "<area 2>", ...],
  "executive_summary": "<3 sentences summarizing performance>"
}"""},
            {"role": "user", "content": summary_context},
        ],
        temperature=0.3,
        max_tokens=800,
        response_format={"type": "json_object"},
    )

    try:
        summary_data = json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        summary_data = {
            "strengths": ["Analysis complete"],
            "areas_for_improvement": ["See category scores for details"],
            "executive_summary": f"The candidate scored {total}/100 ({grade}).",
        }

    print(f"[scorer] ✅ Final score: {total}/100 ({grade})")

    return ScoringReport(
        public_speaking=ps_score,
        answer_quality=aq_score,
        consistency=cs_score,
        filler_assessment=fw_score,
        total_score=total,
        grade=grade,
        strengths=summary_data.get("strengths", []),
        areas_for_improvement=summary_data.get("areas_for_improvement", []),
        executive_summary=summary_data.get("executive_summary", ""),
        questions_evaluated=questions,
        candidate_word_count=diarization.candidate_word_count,
        interviewer_word_count=diarization.interviewer_word_count,
        diarization_confidence=diar_confidence,
    )
