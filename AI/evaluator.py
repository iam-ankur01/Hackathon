"""
evaluator.py
Groq Llama 3.3 70B — answer quality + confidence scoring.
Single API call for both (saves latency).
"""

import os
import json
from dataclasses import dataclass
from typing import List
from groq import Groq


@dataclass
class EvalResult:
    # Quality scores (1–10)
    clarity: int
    depth: int
    relevance: int
    structure: int        # STAR / CAR method usage
    conciseness: int
    confidence: int       # linguistic confidence markers

    # Qualitative
    tone: str             # "confident" | "hesitant" | "rambling" | "assertive"
    hedging_phrases: List[str]    # "I think maybe", "sort of", etc.
    strong_phrases: List[str]     # powerful, assertive moments
    rationale: str        # brief explanation of scores


EVAL_SYSTEM_PROMPT = """You are an expert senior interviewer at a top-tier tech company.
Analyze the interview transcript and return ONLY a valid JSON object — no preamble, no markdown, no explanation outside the JSON.

Score each dimension from 1 to 10 where:
1-3 = poor, 4-6 = average, 7-8 = good, 9-10 = excellent

Definitions:
- clarity: Is the answer easy to understand? Clear language, no rambling.
- depth: Does the candidate go beyond surface-level? Examples, specifics, nuance.
- relevance: Does the answer directly address the question asked?
- structure: Is there a clear framework? (STAR = Situation, Task, Action, Result)
- conciseness: Gets to the point without unnecessary filler content.
- confidence: Assertive language, no excessive hedging, owns their statements.
- tone: Overall delivery — one of: confident / hesitant / rambling / assertive / nervous
- hedging_phrases: List up to 5 exact phrases showing uncertainty (e.g. "I think maybe")
- strong_phrases: List up to 5 exact phrases showing strength/clarity
- rationale: 2-sentence explanation of the scores

Return EXACTLY this JSON structure:
{
  "clarity": <int>,
  "depth": <int>,
  "relevance": <int>,
  "structure": <int>,
  "conciseness": <int>,
  "confidence": <int>,
  "tone": "<string>",
  "hedging_phrases": ["<phrase>", ...],
  "strong_phrases": ["<phrase>", ...],
  "rationale": "<string>"
}"""


def evaluate(transcript: str, question: str = None) -> EvalResult:
    """
    Evaluate interview transcript quality and confidence.
    question: optional interview question for relevance grounding.
    """
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    user_content = ""
    if question:
        user_content += f"INTERVIEW QUESTION:\n{question}\n\n"
    user_content += f"CANDIDATE TRANSCRIPT:\n{transcript}"

    print("[evaluator] Scoring quality + confidence via Llama 3.3 70B...")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": EVAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
        max_tokens=800,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback defaults
        data = {
            "clarity": 5, "depth": 5, "relevance": 5,
            "structure": 5, "conciseness": 5, "confidence": 5,
            "tone": "neutral", "hedging_phrases": [], "strong_phrases": [],
            "rationale": "Could not parse evaluation."
        }

    print(f"[evaluator] Done — clarity={data.get('clarity')}, confidence={data.get('confidence')}")

    return EvalResult(
        clarity=data.get("clarity", 5),
        depth=data.get("depth", 5),
        relevance=data.get("relevance", 5),
        structure=data.get("structure", 5),
        conciseness=data.get("conciseness", 5),
        confidence=data.get("confidence", 5),
        tone=data.get("tone", "neutral"),
        hedging_phrases=data.get("hedging_phrases", []),
        strong_phrases=data.get("strong_phrases", []),
        rationale=data.get("rationale", ""),
    )
