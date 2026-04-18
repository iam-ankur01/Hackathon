"""
speaker_diarizer.py
AI-powered speaker diarization — distinguishes interviewer from candidate.

Uses Groq Llama 3.3 70B to analyze:
  - Question patterns (interviewer asks, candidate answers)
  - Answer patterns (candidate provides explanations, examples)
  - Conversational flow and context
  - Turn-taking dynamics

Outputs structured speaker-labeled transcript with only candidate speech
extracted for scoring.
"""

import os
import json
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from groq import Groq


@dataclass
class SpeakerTurn:
    speaker: str          # "interviewer" | "candidate"
    text: str
    start_time: float     # seconds from audio start
    end_time: float
    confidence: float     # 0.0–1.0, how confident the AI is


@dataclass
class DiarizationResult:
    turns: List[SpeakerTurn]
    candidate_text: str             # all candidate speech concatenated
    interviewer_text: str           # all interviewer speech concatenated
    candidate_word_count: int
    interviewer_word_count: int
    questions_detected: List[str]   # interviewer questions
    total_turns: int
    ambiguous_turns: int            # turns where role was uncertain


DIARIZE_SYSTEM_PROMPT = """You are an expert conversation analyst specializing in interview transcripts.
Your task is to analyze a raw interview transcript and identify which parts are spoken by the INTERVIEWER 
and which parts are spoken by the CANDIDATE.

Use these signals to distinguish speakers:

INTERVIEWER signals:
- Asks questions (who, what, why, how, tell me about, describe, can you explain)
- Sets context ("Let's move on to...", "Now I'd like to ask about...")
- Short prompts ("Okay", "Great", "Interesting", "Go ahead")
- Follow-up questions ("Can you elaborate?", "What about...")
- Evaluative comments ("That's interesting", "I see")
- Opens/closes the interview ("Welcome", "Thank you for your time")

CANDIDATE signals:
- Provides detailed answers and explanations
- Shares personal experiences ("In my previous role...", "I worked on...")
- Describes technical implementations
- Uses STAR method (Situation, Task, Action, Result)
- Longer response segments following a question
- Self-referential language ("I built...", "My approach was...")

RULES:
1. The first substantive question usually comes from the interviewer
2. Longer passages after a question are typically candidate answers
3. If the transcript has clear speaker labels (Speaker 1, Speaker 2, etc.), map them correctly
4. Handle ambiguous turns by analyzing surrounding context
5. Mark confidence level for each turn

Return ONLY valid JSON. No markdown. No preamble.

{
  "turns": [
    {
      "speaker": "interviewer" | "candidate",
      "text": "<exact text from transcript>",
      "confidence": <float 0.0-1.0>
    }
  ],
  "questions_detected": ["<question 1>", "<question 2>", ...],
  "reasoning": "<brief explanation of how you identified speakers>"
}"""


DIARIZE_WITH_JD_PROMPT = """You are an expert conversation analyst specializing in interview transcripts.
Your task is to analyze a raw interview transcript and identify which parts are spoken by the INTERVIEWER 
and which parts are spoken by the CANDIDATE.

You are also given the JOB DESCRIPTION for context. The interviewer's questions will likely relate to 
this role, and the candidate's answers will attempt to demonstrate fitness for this position.

Use these signals to distinguish speakers:

INTERVIEWER signals:
- Asks questions relevant to the job description
- Questions about skills, experience, and competencies listed in the JD
- Sets context and transitions between topics
- Short acknowledgments and follow-ups

CANDIDATE signals:
- Provides detailed answers demonstrating relevant experience
- References skills matching the job description
- Shares personal experiences and achievements
- Describes technical implementations and projects

RULES:
1. The first substantive question usually comes from the interviewer
2. Longer passages after a question are typically candidate answers
3. If the transcript has clear speaker labels, map them correctly
4. Handle ambiguous turns by analyzing surrounding context  
5. Mark confidence level for each turn

Return ONLY valid JSON. No markdown. No preamble.

{
  "turns": [
    {
      "speaker": "interviewer" | "candidate",
      "text": "<exact text from transcript>",
      "confidence": <float 0.0-1.0>
    }
  ],
  "questions_detected": ["<question 1>", "<question 2>", ...],
  "reasoning": "<brief explanation of how you identified speakers>"
}"""


def _preprocess_transcript(transcript: str) -> str:
    """
    Pre-process transcript to detect any existing speaker labels
    and normalize the format for AI analysis.
    """
    # Common patterns for pre-labeled transcripts
    label_patterns = [
        r'(Speaker\s*\d+)\s*:\s*',
        r'(Person\s*[A-Z])\s*:\s*',
        r'(Interviewer|Candidate|Host|Guest)\s*:\s*',
        r'\[?(Speaker\s*\d+)\]?\s*:\s*',
    ]

    for pattern in label_patterns:
        if re.search(pattern, transcript, re.IGNORECASE):
            return transcript  # already has labels, pass as-is

    # If no labels found, try to split on natural turn boundaries
    # (long pauses, topic changes, question marks followed by new sentences)
    return transcript


def _parse_json_transcript(json_content: str) -> str:
    """
    Parse a JSON transcript file into a plain text transcript.
    Handles common formats:
      - [{speaker, text, timestamp}, ...]
      - {transcript: [{...}]}
      - {segments: [{...}]}
    """
    try:
        data = json.loads(json_content)
    except json.JSONDecodeError:
        return json_content  # Not valid JSON, return as-is

    segments = []

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                speaker = item.get("speaker", item.get("role", ""))
                text = item.get("text", item.get("content", item.get("transcript", "")))
                if speaker:
                    segments.append(f"{speaker}: {text}")
                else:
                    segments.append(text)
    elif isinstance(data, dict):
        # Try common wrapper keys
        items = data.get("transcript", data.get("segments", data.get("turns", [])))
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    speaker = item.get("speaker", item.get("role", ""))
                    text = item.get("text", item.get("content", ""))
                    if speaker:
                        segments.append(f"{speaker}: {text}")
                    else:
                        segments.append(text)
        elif isinstance(items, str):
            return items

    return "\n\n".join(segments) if segments else str(data)


def diarize(transcript: str, job_description: str = None,
            word_timestamps: List[Dict] = None) -> DiarizationResult:
    """
    Analyze a raw transcript and separate interviewer vs candidate speech.

    Args:
        transcript       : raw transcript text (or JSON string)
        job_description  : optional JD for context-aware diarization
        word_timestamps  : optional [{word, start, end}, ...] for timing

    Returns:
        DiarizationResult with separated speaker turns
    """
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    # Handle JSON transcripts
    if transcript.strip().startswith(("{", "[")):
        transcript = _parse_json_transcript(transcript)

    processed = _preprocess_transcript(transcript)

    # Choose prompt based on whether JD is available
    if job_description:
        system_prompt = DIARIZE_WITH_JD_PROMPT
        user_content = f"JOB DESCRIPTION:\n{job_description}\n\nINTERVIEW TRANSCRIPT:\n{processed}"
    else:
        system_prompt = DIARIZE_SYSTEM_PROMPT
        user_content = f"INTERVIEW TRANSCRIPT:\n{processed}"

    # Truncate if very long (Llama context window management)
    max_chars = 28000
    if len(user_content) > max_chars:
        user_content = user_content[:max_chars] + "\n\n[TRANSCRIPT TRUNCATED — analyze what is provided]"

    print("[diarizer] Analyzing speaker roles via Llama 3.3 70B...")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.15,
        max_tokens=4000,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: treat entire transcript as candidate speech
        print("[diarizer] ⚠ Could not parse AI response, treating all as candidate speech")
        return DiarizationResult(
            turns=[SpeakerTurn("candidate", transcript, 0.0, 0.0, 0.5)],
            candidate_text=transcript,
            interviewer_text="",
            candidate_word_count=len(transcript.split()),
            interviewer_word_count=0,
            questions_detected=[],
            total_turns=1,
            ambiguous_turns=1,
        )

    # Parse turns
    turns: List[SpeakerTurn] = []
    candidate_parts = []
    interviewer_parts = []
    ambiguous = 0
    current_time = 0.0

    for t in data.get("turns", []):
        speaker = t.get("speaker", "candidate").lower().strip()
        text = t.get("text", "").strip()
        confidence = float(t.get("confidence", 0.8))

        if not text:
            continue

        # Normalize speaker label
        if speaker in ("interviewer", "host", "speaker 1", "person a"):
            speaker = "interviewer"
        else:
            speaker = "candidate"

        if confidence < 0.6:
            ambiguous += 1

        # Estimate timing from word count (rough heuristic)
        word_count = len(text.split())
        duration_estimate = word_count / 2.5  # ~150 wpm = 2.5 words/sec
        end_time = current_time + duration_estimate

        turns.append(SpeakerTurn(
            speaker=speaker,
            text=text,
            start_time=round(current_time, 2),
            end_time=round(end_time, 2),
            confidence=confidence,
        ))

        if speaker == "candidate":
            candidate_parts.append(text)
        else:
            interviewer_parts.append(text)

        current_time = end_time + 0.5  # small gap between turns

    candidate_text = " ".join(candidate_parts)
    interviewer_text = " ".join(interviewer_parts)

    questions = data.get("questions_detected", [])

    print(f"[diarizer] Done — {len(turns)} turns detected "
          f"({len(candidate_parts)} candidate, {len(interviewer_parts)} interviewer)")
    if questions:
        print(f"[diarizer] Questions detected: {len(questions)}")

    return DiarizationResult(
        turns=turns,
        candidate_text=candidate_text,
        interviewer_text=interviewer_text,
        candidate_word_count=len(candidate_text.split()),
        interviewer_word_count=len(interviewer_text.split()),
        questions_detected=questions,
        total_turns=len(turns),
        ambiguous_turns=ambiguous,
    )
