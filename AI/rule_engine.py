"""
rule_engine.py
Pure Python — zero API calls.
Detects: filler words, pauses, WPM, vocabulary richness.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict

# ── Filler word list ──────────────────────────────────────────────────────────
FILLERS = {
    "um", "uh", "umm", "uhh", "hmm", "er", "err",
    "like", "basically", "literally", "honestly", "actually",
    "you know", "i mean", "right", "okay so", "so yeah",
    "kind of", "kinda", "sort of", "sorta",
    "you see", "the thing is", "i guess", "i suppose",
}

MULTI_WORD_FILLERS = [f for f in FILLERS if " " in f]
SINGLE_WORD_FILLERS = {f for f in FILLERS if " " not in f}


@dataclass
class FillerHit:
    word: str
    position: int          # word index in transcript


@dataclass
class PauseHit:
    gap_seconds: float
    after_word: str
    severity: str          # "normal" | "significant" | "long"


@dataclass
class RuleAnalysis:
    # Filler stats
    filler_hits: List[FillerHit]
    filler_count: int
    filler_rate_per_min: float
    filler_percentage: float       # % of total words

    # Pause stats
    pause_hits: List[PauseHit]
    pause_count: int
    significant_pause_count: int   # > 3s
    avg_pause_seconds: float

    # Speed stats
    wpm: float
    total_words: int
    duration_seconds: float

    # Vocabulary
    type_token_ratio: float        # vocabulary richness 0–1
    unique_words: int

    # Highlighted transcript (fillers wrapped in markers)
    highlighted_transcript: str

    # Human-readable summary
    speed_label: str               # "too slow" | "good" | "too fast"
    filler_label: str              # "excellent" | "good" | "needs work" | "poor"


def analyze(transcript: str, word_timestamps: List[Dict] = None,
            duration_seconds: float = None) -> RuleAnalysis:
    """
    transcript       : plain text string
    word_timestamps  : list of {word, start, end} dicts from Groq Whisper
    duration_seconds : total audio length
    """

    words = transcript.split()
    total_words = len(words)

    # ── Filler detection ──────────────────────────────────────────────────────
    filler_hits: List[FillerHit] = []
    text_lower = transcript.lower()

    # Multi-word fillers first (word boundaries)
    for mf in MULTI_WORD_FILLERS:
        pattern = re.compile(r'\b' + re.escape(mf) + r'\b', re.IGNORECASE)
        for m in pattern.finditer(text_lower):
            word_pos = len(text_lower[:m.start()].split())
            filler_hits.append(FillerHit(word=mf, position=word_pos))

    # Single-word fillers — only exact word matches
    for i, w in enumerate(words):
        clean = re.sub(r"[^a-z]", "", w.lower())
        if clean in SINGLE_WORD_FILLERS:
            filler_hits.append(FillerHit(word=clean, position=i))

    filler_hits.sort(key=lambda x: x.position)
    filler_count = len(filler_hits)

    # ── Pause detection ───────────────────────────────────────────────────────
    pause_hits: List[PauseHit] = []
    if word_timestamps and len(word_timestamps) > 1:
        for i in range(1, len(word_timestamps)):
            prev = word_timestamps[i - 1]
            curr = word_timestamps[i]
            gap = curr.get("start", 0) - prev.get("end", 0)
            if gap >= 1.5:
                severity = "long" if gap > 4 else "significant" if gap > 3 else "normal"
                pause_hits.append(PauseHit(
                    gap_seconds=round(gap, 2),
                    after_word=prev.get("word", ""),
                    severity=severity
                ))

    pause_count = len(pause_hits)
    significant_pause_count = sum(1 for p in pause_hits if p.severity != "normal")
    avg_pause = (
        round(sum(p.gap_seconds for p in pause_hits) / pause_count, 2)
        if pause_count else 0.0
    )

    # ── Duration & WPM ────────────────────────────────────────────────────────
    if duration_seconds is None and word_timestamps:
        duration_seconds = word_timestamps[-1].get("end", 60)
    if duration_seconds is None:
        duration_seconds = 60  # fallback

    duration_min = max(duration_seconds / 60, 0.01)
    wpm = round(total_words / duration_min, 1)
    filler_rate = round(filler_count / duration_min, 2)
    filler_pct = round((filler_count / max(total_words, 1)) * 100, 1)

    # ── Vocabulary richness ───────────────────────────────────────────────────
    clean_words = [re.sub(r"[^a-z]", "", w.lower()) for w in words]
    clean_words = [w for w in clean_words if len(w) > 1]
    unique_words = len(set(clean_words))
    ttr = round(unique_words / max(len(clean_words), 1), 3)

    # ── Highlighted transcript ────────────────────────────────────────────────
    highlighted = transcript
    for f in sorted(FILLERS, key=len, reverse=True):
        pattern = re.compile(r'\b' + re.escape(f) + r'\b', re.IGNORECASE)
        highlighted = pattern.sub(f"[FILLER:{f.upper()}]", highlighted)

    # ── Labels ───────────────────────────────────────────────────────────────
    if wpm < 110:
        speed_label = "too slow"
    elif wpm > 165:
        speed_label = "too fast"
    else:
        speed_label = "good pace"

    if filler_rate < 2:
        filler_label = "excellent"
    elif filler_rate < 4:
        filler_label = "good"
    elif filler_rate < 8:
        filler_label = "needs work"
    else:
        filler_label = "poor"

    return RuleAnalysis(
        filler_hits=filler_hits,
        filler_count=filler_count,
        filler_rate_per_min=filler_rate,
        filler_percentage=filler_pct,
        pause_hits=pause_hits,
        pause_count=pause_count,
        significant_pause_count=significant_pause_count,
        avg_pause_seconds=avg_pause,
        wpm=wpm,
        total_words=total_words,
        duration_seconds=duration_seconds,
        type_token_ratio=ttr,
        unique_words=unique_words,
        highlighted_transcript=highlighted,
        speed_label=speed_label,
        filler_label=filler_label,
    )
