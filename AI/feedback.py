"""
feedback.py
Groq Llama 3.3 70B — final coach-level debrief synthesis.
Takes all prior analysis and generates structured, actionable feedback.
"""

import os
import json
from dataclasses import dataclass
from typing import List, Dict
from groq import Groq
from rule_engine import RuleAnalysis
from evaluator import EvalResult


@dataclass
class Strength:
    title: str
    detail: str
    evidence: str        # exact quote from transcript


@dataclass
class Improvement:
    issue: str
    why_it_matters: str
    how_to_fix: str
    rewrite_example: str   # AI-rewritten version of their bad moment


@dataclass
class FeedbackReport:
    overall_score: int           # 0–100
    grade: str                   # A+, A, B+, B, C+, C, D, F
    executive_summary: str       # 3-sentence overview
    strengths: List[Strength]
    improvements: List[Improvement]
    best_moment: Dict            # {quote, why_it_worked}
    worst_moment: Dict           # {quote, what_went_wrong}
    one_thing_to_fix: str        # single most impactful change
    next_steps: List[str]        # 3 concrete action items


FEEDBACK_SYSTEM_PROMPT = """You are a brutally honest, world-class interview coach. 
You have coached candidates into Google, Meta, and McKinsey.
You give specific, evidence-based feedback — you always quote exact phrases from the transcript.
You are direct but constructive. You never give generic advice.

Return ONLY valid JSON. No markdown. No preamble. Exactly this structure:

{
  "overall_score": <int 0-100>,
  "grade": "<A+|A|B+|B|C+|C|D|F>",
  "executive_summary": "<3 sentences: what went well, what didn't, biggest opportunity>",
  "strengths": [
    {
      "title": "<short title>",
      "detail": "<1-2 sentences>",
      "evidence": "<exact quote from transcript>"
    }
  ],
  "improvements": [
    {
      "issue": "<short title of problem>",
      "why_it_matters": "<why this hurts them in an interview>",
      "how_to_fix": "<specific technique or framework>",
      "rewrite_example": "<rewrite their actual words better>"
    }
  ],
  "best_moment": {
    "quote": "<exact quote from transcript>",
    "why_it_worked": "<explanation>"
  },
  "worst_moment": {
    "quote": "<exact quote from transcript>",
    "what_went_wrong": "<explanation>"
  },
  "one_thing_to_fix": "<the single most impactful change they can make>",
  "next_steps": ["<action 1>", "<action 2>", "<action 3>"]
}

Generate 2-3 strengths and 2-4 improvements. Be specific. Quote the transcript."""


def _compute_score(rule: RuleAnalysis, ev: EvalResult) -> int:
    """Weighted formula: 60% content quality, 40% communication."""
    content = (ev.clarity + ev.depth + ev.relevance + ev.structure + ev.conciseness) / 5
    comm_raw = ev.confidence

    # WPM penalty
    wpm_penalty = 0
    if rule.wpm < 100 or rule.wpm > 180:
        wpm_penalty = 10
    elif rule.wpm < 120 or rule.wpm > 165:
        wpm_penalty = 5

    # Filler penalty (per minute)
    filler_penalty = min(rule.filler_rate_per_min * 1.5, 20)

    # Pause penalty
    pause_penalty = min(rule.significant_pause_count * 3, 15)

    comm_score = max(0, (comm_raw / 10 * 100) - wpm_penalty - filler_penalty - pause_penalty)
    content_score = content / 10 * 100

    final = round((content_score * 0.6) + (comm_score * 0.4))
    return max(0, min(100, final))


def _score_to_grade(score: int) -> str:
    if score >= 93: return "A+"
    if score >= 87: return "A"
    if score >= 80: return "B+"
    if score >= 73: return "B"
    if score >= 66: return "C+"
    if score >= 60: return "C"
    if score >= 50: return "D"
    return "F"


def generate(transcript: str, rule: RuleAnalysis,
             ev: EvalResult, question: str = None) -> FeedbackReport:
    """Generate full coach-level debrief from all analysis inputs."""
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    overall_score = _compute_score(rule, ev)
    grade = _score_to_grade(overall_score)

    # Build rich context for Llama
    context = f"""
INTERVIEW QUESTION: {question or "Not provided"}

CANDIDATE TRANSCRIPT:
{transcript}

COMMUNICATION METRICS:
- Words per minute: {rule.wpm} ({rule.speed_label})
- Filler words: {rule.filler_count} total ({rule.filler_rate_per_min}/min) — Rating: {rule.filler_label}
- Filler word list used: {', '.join(set(h.word for h in rule.filler_hits[:10]))}
- Pauses (>1.5s): {rule.pause_count} total, {rule.significant_pause_count} significant (>3s)
- Vocabulary richness (TTR): {rule.type_token_ratio} (0=repetitive, 1=diverse)
- Total words: {rule.total_words}

QUALITY SCORES (1-10):
- Clarity: {ev.clarity}/10
- Depth: {ev.depth}/10
- Relevance: {ev.relevance}/10
- Structure (STAR): {ev.structure}/10
- Conciseness: {ev.conciseness}/10
- Confidence: {ev.confidence}/10
- Tone detected: {ev.tone}

HEDGING PHRASES DETECTED: {', '.join(ev.hedging_phrases) or 'None'}
STRONG PHRASES DETECTED: {', '.join(ev.strong_phrases) or 'None'}

PRE-COMPUTED SCORE: {overall_score}/100 (Grade: {grade})

Generate brutally honest, specific, transcript-quoted feedback now.
"""

    print("[feedback] Generating coach debrief via Llama 3.3 70B...")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": FEEDBACK_SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ],
        temperature=0.4,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {
            "overall_score": overall_score,
            "grade": grade,
            "executive_summary": "Analysis complete. See metrics above for details.",
            "strengths": [],
            "improvements": [],
            "best_moment": {"quote": "", "why_it_worked": ""},
            "worst_moment": {"quote": "", "what_went_wrong": ""},
            "one_thing_to_fix": "Reduce filler words and use STAR method.",
            "next_steps": ["Practice mock interviews", "Record yourself", "Use STAR framework"]
        }

    print(f"[feedback] Done — Score: {data.get('overall_score')}, Grade: {data.get('grade')}")

    # Parse nested structures safely
    strengths = [
        Strength(
            title=s.get("title", ""),
            detail=s.get("detail", ""),
            evidence=s.get("evidence", "")
        )
        for s in data.get("strengths", [])
    ]

    improvements = [
        Improvement(
            issue=i.get("issue", ""),
            why_it_matters=i.get("why_it_matters", ""),
            how_to_fix=i.get("how_to_fix", ""),
            rewrite_example=i.get("rewrite_example", "")
        )
        for i in data.get("improvements", [])
    ]

    return FeedbackReport(
        overall_score=data.get("overall_score", overall_score),
        grade=data.get("grade", grade),
        executive_summary=data.get("executive_summary", ""),
        strengths=strengths,
        improvements=improvements,
        best_moment=data.get("best_moment", {}),
        worst_moment=data.get("worst_moment", {}),
        one_thing_to_fix=data.get("one_thing_to_fix", ""),
        next_steps=data.get("next_steps", []),
    )
