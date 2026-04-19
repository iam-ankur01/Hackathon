"""
pipeline.py
Antigravity AI — master pipeline.
One function call = full interview analysis.

Usage:
    from pipeline import analyze
    result = analyze("interview.mp3", question="Tell me about yourself")
    print(result)
"""

import os
import json
import time
from dotenv import load_dotenv
from dataclasses import dataclass, asdict
from typing import Optional

load_dotenv()  # loads GROQ_API_KEY from .env

from transcriber import transcribe
from rule_engine import analyze as rule_analyze
from evaluator import evaluate
from feedback import generate, FeedbackReport


@dataclass
class AntigravityResult:
    # ── Meta ───────────────────────────────────────────────────
    audio_file: str
    question: Optional[str]
    processing_time_seconds: float

    # ── Scores ─────────────────────────────────────────────────
    overall_score: int
    grade: str

    # ── Communication metrics ──────────────────────────────────
    wpm: float
    speed_label: str
    filler_count: int
    filler_rate_per_min: float
    filler_percentage: float
    pause_count: int
    significant_pause_count: int
    avg_pause_seconds: float
    vocabulary_richness: float     # TTR 0–1

    # ── Quality scores (1–10) ──────────────────────────────────
    clarity: int
    depth: int
    relevance: int
    structure: int
    conciseness: int
    confidence: int
    tone: str

    # ── Qualitative insights ───────────────────────────────────
    executive_summary: str
    strengths: list
    improvements: list
    best_moment: dict
    worst_moment: dict
    one_thing_to_fix: str
    next_steps: list
    hedging_phrases: list
    strong_phrases: list

    # ── Transcript ─────────────────────────────────────────────
    transcript: str
    highlighted_transcript: str    # fillers marked with [FILLER:WORD]

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(asdict(self), indent=indent, ensure_ascii=False)

    def print_report(self):
        """Pretty-print the full report to terminal."""
        divider = "─" * 60

        print(f"\n{'═' * 60}")
        print(f"  ANTIGRAVITY — INTERVIEW DEBRIEF")
        print(f"{'═' * 60}")

        print(f"\n📁 File    : {self.audio_file}")
        if self.question:
            print(f"❓ Question: {self.question}")
        print(f"⏱  Analyzed in {self.processing_time_seconds:.1f}s\n")

        # Score
        bar_filled = int(self.overall_score / 5)
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        print(f"  OVERALL SCORE: {self.overall_score}/100   Grade: {self.grade}")
        print(f"  [{bar}]")

        # Communication
        print(f"\n{divider}")
        print("  COMMUNICATION METRICS")
        print(f"{divider}")
        print(f"  Speech Rate   : {self.wpm} WPM  ({self.speed_label})")
        print(f"  Filler Words  : {self.filler_count} total ({self.filler_rate_per_min}/min)  [{self.filler_percentage}% of words]")
        print(f"  Pauses (>1.5s): {self.pause_count} total, {self.significant_pause_count} significant")
        if self.avg_pause_seconds:
            print(f"  Avg Pause     : {self.avg_pause_seconds}s")
        print(f"  Vocabulary    : {self.vocabulary_richness:.2f} TTR  (1.0 = maximally diverse)")
        print(f"  Tone Detected : {self.tone}")

        # Quality
        print(f"\n{divider}")
        print("  QUALITY SCORES")
        print(f"{divider}")
        dims = [
            ("Clarity",     self.clarity),
            ("Depth",       self.depth),
            ("Relevance",   self.relevance),
            ("Structure",   self.structure),
            ("Conciseness", self.conciseness),
            ("Confidence",  self.confidence),
        ]
        for name, score in dims:
            filled = "█" * score + "░" * (10 - score)
            print(f"  {name:<12} [{filled}] {score}/10")

        # Summary
        print(f"\n{divider}")
        print("  EXECUTIVE SUMMARY")
        print(f"{divider}")
        print(f"  {self.executive_summary}\n")

        # Strengths
        if self.strengths:
            print(f"  ✅ STRENGTHS")
            for s in self.strengths:
                print(f"\n  • {s['title']}")
                print(f"    {s['detail']}")
                if s.get("evidence"):
                    print(f"    Quote: \"{s['evidence'][:100]}...\"")

        # Improvements
        if self.improvements:
            print(f"\n  ⚠️  IMPROVEMENTS")
            for i, imp in enumerate(self.improvements, 1):
                print(f"\n  {i}. {imp['issue']}")
                print(f"     WHY IT MATTERS : {imp['why_it_matters']}")
                print(f"     HOW TO FIX     : {imp['how_to_fix']}")
                if imp.get("rewrite_example"):
                    print(f"     BETTER VERSION : \"{imp['rewrite_example'][:120]}\"")

        # Best / worst moment
        print(f"\n{divider}")
        print("  KEY MOMENTS")
        print(f"{divider}")
        if self.best_moment.get("quote"):
            print(f"\n  🌟 BEST MOMENT")
            print(f"     \"{self.best_moment['quote'][:120]}\"")
            print(f"     → {self.best_moment.get('why_it_worked', '')}")
        if self.worst_moment.get("quote"):
            print(f"\n  ❌ WORST MOMENT")
            print(f"     \"{self.worst_moment['quote'][:120]}\"")
            print(f"     → {self.worst_moment.get('what_went_wrong', '')}")

        # One thing
        print(f"\n{divider}")
        print(f"  💡 #1 THING TO FIX")
        print(f"{divider}")
        print(f"  {self.one_thing_to_fix}")

        # Next steps
        print(f"\n{divider}")
        print("  NEXT STEPS")
        print(f"{divider}")
        for step in self.next_steps:
            print(f"  → {step}")

        # Hedging
        if self.hedging_phrases:
            print(f"\n  ⚠️  Hedging phrases detected: {', '.join(self.hedging_phrases)}")
        if self.strong_phrases:
            print(f"  💪 Strong phrases detected: {', '.join(self.strong_phrases)}")

        print(f"\n{'═' * 60}\n")


def analyze(audio_path: str, question: str = None,
            language: str = "en") -> AntigravityResult:
    """
    Full Antigravity pipeline.

    Args:
        audio_path : path to audio/video file (mp3, mp4, wav, webm, m4a)
        question   : optional interview question asked to candidate
        language   : language code (default "en")

    Returns:
        AntigravityResult with all metrics and feedback
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if not os.environ.get("GROQ_API_KEY"):
        raise EnvironmentError("GROQ_API_KEY not set. Add it to .env file.")

    start = time.time()

    # ── Step 1: Transcribe ────────────────────────────────────────────────────
    print("\n[pipeline] Step 1/3 — Transcribing audio...")
    transcript_result = transcribe(audio_path, language=language)

    # ── Step 2: Rule engine (instant, no API) ─────────────────────────────────
    print("[pipeline] Step 2/3 — Running rule analysis...")
    rule = rule_analyze(
        transcript=transcript_result.text,
        word_timestamps=transcript_result.word_timestamps,
        duration_seconds=transcript_result.duration_seconds,
    )

    # ── Step 3a: Evaluate quality + confidence ────────────────────────────────
    print("[pipeline] Step 3a/3 — Evaluating quality + confidence...")
    ev = evaluate(transcript=transcript_result.text, question=question)

    # ── Step 3b: Generate debrief ─────────────────────────────────────────────
    print("[pipeline] Step 3b/3 — Generating coach debrief...")
    report = generate(
        transcript=transcript_result.text,
        rule=rule,
        ev=ev,
        question=question,
    )

    elapsed = round(time.time() - start, 2)

    # ── Assemble final result ─────────────────────────────────────────────────
    return AntigravityResult(
        audio_file=audio_path,
        question=question,
        processing_time_seconds=elapsed,

        overall_score=report.overall_score,
        grade=report.grade,

        wpm=rule.wpm,
        speed_label=rule.speed_label,
        filler_count=rule.filler_count,
        filler_rate_per_min=rule.filler_rate_per_min,
        filler_percentage=rule.filler_percentage,
        pause_count=rule.pause_count,
        significant_pause_count=rule.significant_pause_count,
        avg_pause_seconds=rule.avg_pause_seconds,
        vocabulary_richness=rule.type_token_ratio,

        clarity=ev.clarity,
        depth=ev.depth,
        relevance=ev.relevance,
        structure=ev.structure,
        conciseness=ev.conciseness,
        confidence=ev.confidence,
        tone=ev.tone,

        executive_summary=report.executive_summary,
        strengths=[{"title": s.title, "detail": s.detail, "evidence": s.evidence}
                   for s in report.strengths],
        improvements=[{"issue": i.issue, "why_it_matters": i.why_it_matters,
                        "how_to_fix": i.how_to_fix, "rewrite_example": i.rewrite_example}
                      for i in report.improvements],
        best_moment=report.best_moment,
        worst_moment=report.worst_moment,
        one_thing_to_fix=report.one_thing_to_fix,
        next_steps=report.next_steps,
        hedging_phrases=ev.hedging_phrases,
        strong_phrases=ev.strong_phrases,

        transcript=transcript_result.text,
        highlighted_transcript=rule.highlighted_transcript,
    )


# ── CLI entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <audio_file> [interview_question]")
        print("Example: python pipeline.py interview.mp3 'Tell me about yourself'")
        sys.exit(1)

    audio = sys.argv[1]
    q = sys.argv[2] if len(sys.argv) > 2 else None

    result = analyze(audio, question=q)

    # Print beautiful report
    result.print_report()

    # Also save JSON
    out_path = audio.rsplit(".", 1)[0] + "_feedback.json"
    with open(out_path, "w") as f:
        f.write(result.to_json())
    print(f"[pipeline] JSON saved → {out_path}")
