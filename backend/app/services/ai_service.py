"""Wrap the AI interview evaluation pipeline."""
import json
import os
import sys
from typing import List, Optional

# Make the AI/ folder importable
_AI_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "AI"))
if _AI_DIR not in sys.path:
    sys.path.insert(0, _AI_DIR)

# Ensure GROQ_API_KEY is available in os.environ even before the AI pipeline
# is first invoked (the coach-chat and roadmap endpoints need it up front).
try:
    from dotenv import load_dotenv
    load_dotenv()  # backend/.env
    load_dotenv(os.path.join(_AI_DIR, ".env"))  # AI/.env as a fallback
except Exception:
    pass
if not os.environ.get("GROQ_API_KEY"):
    try:
        from ..config import settings as _settings  # type: ignore
        if getattr(_settings, "GROQ_API_KEY", ""):
            os.environ["GROQ_API_KEY"] = _settings.GROQ_API_KEY
    except Exception:
        pass


_GROQ_MODEL = "llama-3.3-70b-versatile"


def _get_groq_client():
    """Lazy-create a Groq client using the same key the pipeline uses."""
    from groq import Groq
    return Groq(api_key=os.environ["GROQ_API_KEY"])


def run_pipeline(
    interview_path: str,
    job_description: str = "",
    job_title: str = "",
    company_name: str = "",
    resume_path: Optional[str] = None,
    github_url: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    transcript_text: Optional[str] = None,
) -> dict:
    """Run the full evaluation pipeline and return a serializable report dict."""
    from pipeline_v2 import evaluate_interview  # lazy import

    report = evaluate_interview(
        interview_path=interview_path,
        job_description=job_description,
        job_title=job_title,
        company_name=company_name,
        resume_path=resume_path,
        github_url=github_url,
        linkedin_url=linkedin_url,
        transcript_text=transcript_text,
    )
    return report.to_dict()


def generate_coach_tips(report: dict) -> dict:
    """Given a scoring report, produce actionable coaching suggestions."""
    cat = report.get("category_breakdown", {})
    tips = []
    if cat.get("filler_word_assessment", {}).get("score", 10) < 7:
        tips.append({
            "area": "Filler Words",
            "tip": "Practice pausing instead of saying 'um' or 'like'. Record yourself for 2 min daily.",
        })
    if cat.get("public_speaking", {}).get("score", 30) < 20:
        tips.append({
            "area": "Public Speaking",
            "tip": "Work on pacing and confident tone — try the STAR method for structured answers.",
        })
    if cat.get("answer_quality", {}).get("score", 40) < 28:
        tips.append({
            "area": "Answer Quality",
            "tip": "Directly address the question first, then support with examples tied to the job description.",
        })
    if cat.get("consistency_truthfulness", {}).get("score", 20) < 14:
        tips.append({
            "area": "Consistency",
            "tip": "Align stories with your resume and GitHub — use real project names and concrete numbers.",
        })
    return {
        "tips": tips,
        "improvement_areas": report.get("areas_for_improvement", []),
        "strengths": report.get("strengths", []),
    }


# ── Dynamic Roadmap ──────────────────────────────────────────────────────────

_CATEGORY_LABELS = {
    "public_speaking": "Public Speaking",
    "answer_quality": "Answer Quality",
    "consistency_truthfulness": "Consistency & Truthfulness",
    "filler_word_assessment": "Filler Words",
}

_FALLBACK_TASKS = {
    "public_speaking": [
        {
            "title": "Record & diagnose a 2-minute answer",
            "detail": "Pick a common question (e.g. 'Tell me about yourself'), record on your phone, then replay with a timer. Count fillers, mark 3 spots where pace dropped, and write one concrete change for tomorrow.",
        },
        {
            "title": "STAR delivery drill with deliberate pauses",
            "detail": "Pick one past project. Say it aloud in under 90 seconds using Situation-Task-Action-Result. Insert a full 1-second pause between each letter. Repeat 3 times; the goal is a calm, structured cadence, not speed.",
        },
        {
            "title": "Mirror confidence reps (5 minutes)",
            "detail": "Stand, shoulders back, eye contact with the mirror. Answer 'Why this role?' three different ways. Focus on steady tone, open posture, and ending each answer with a clear full stop instead of trailing off.",
        },
    ],
    "answer_quality": [
        {
            "title": "Write 3 STAR answers tailored to the JD",
            "detail": "Pick the 3 most critical bullet points in the job description. For each, write a 4-sentence STAR answer that uses a real project of yours and ends with a concrete, quantified result (%, $, users, latency).",
        },
        {
            "title": "30-minute deep dive on one JD-critical topic",
            "detail": "Choose the single technical topic from the JD you are weakest on. Read the official docs, build one minimal code example, and write a 5-sentence explainer you could say out loud in an interview.",
        },
        {
            "title": "Rewrite your weakest past answer",
            "detail": "Open your latest interview transcript, pick the answer that scored lowest on answer_quality, and rewrite it: lead with a one-line direct answer, follow with 2-3 sentences of evidence, and end with impact tied to the JD.",
        },
    ],
    "consistency_truthfulness": [
        {
            "title": "Quantify one resume bullet",
            "detail": "Pick one vague resume line. Add a measurable outcome — percentage, time saved, revenue, users impacted, or a before/after number. If you don't know the number, estimate defensibly and note the assumption.",
        },
        {
            "title": "Polish one GitHub project README",
            "detail": "Open your most relevant repo. Rewrite the README to include: a 2-sentence problem statement, tech stack, your specific contribution, and a screenshot or short demo link. Commit the change today.",
        },
        {
            "title": "Align LinkedIn ↔ resume for one role",
            "detail": "Pick one past job. Make the LinkedIn bullet points match your resume word-for-word on dates, title, and scope. Any story you plan to tell in the interview must be verifiable from both documents.",
        },
    ],
    "filler_word_assessment": [
        {
            "title": "Silent pause drill (2 minutes)",
            "detail": "Set a 2-minute timer. Answer 'Walk me through your resume' out loud. Every time you feel an 'um' coming, close your mouth and wait one full second instead. Record it and count how many you caught.",
        },
        {
            "title": "Read aloud + transcript mark-up (10 min)",
            "detail": "Read a technical article aloud for 10 minutes while recording. Transcribe it (or use any speech-to-text). Highlight every filler word in red and note the 3 sentence shapes that triggered the most fillers.",
        },
        {
            "title": "60-second self-intro, under 2 fillers/min",
            "detail": "Record a 60-second self-introduction. Transcribe, count fillers, and re-record until you hit <2 fillers per minute for two takes in a row. Save the best take as your baseline for next week.",
        },
    ],
}


def _rank_weaknesses(report: dict) -> List[str]:
    """Return category keys sorted from weakest to strongest (by score/max)."""
    cb = report.get("category_breakdown", {}) or {}
    ranked = []
    for key, val in cb.items():
        if not isinstance(val, dict):
            continue
        mx = val.get("max") or 0
        if not mx:
            continue
        pct = (val.get("score") or 0) / mx
        ranked.append((pct, key))
    ranked.sort(key=lambda x: x[0])
    return [k for _, k in ranked]


def _fallback_roadmap(report: dict, days: int) -> dict:
    """Deterministic roadmap when the LLM call fails or key is missing."""
    weak = _rank_weaknesses(report)
    if not weak:
        weak = ["answer_quality"]
    weak_areas = [k for k in weak if k in _FALLBACK_TASKS] or ["answer_quality"]

    plan = []
    for i in range(days):
        focus_key = weak_areas[i % len(weak_areas)]
        tasks_pool = _FALLBACK_TASKS.get(focus_key, _FALLBACK_TASKS["answer_quality"])
        # Rotate through the pool so consecutive days on the same focus don't repeat.
        rotated = [
            tasks_pool[(i + 0) % len(tasks_pool)],
            tasks_pool[(i + 1) % len(tasks_pool)],
            tasks_pool[(i + 2) % len(tasks_pool)],
        ]
        plan.append({
            "day": i + 1,
            "focus_area": _CATEGORY_LABELS.get(focus_key, focus_key),
            "tasks": [dict(t) for t in rotated],
            "time_estimate_minutes": 60,
        })

    return {
        "primary_focus": _CATEGORY_LABELS.get(weak_areas[0], weak_areas[0]),
        "summary": f"{days}-day plan focused on {', '.join(_CATEGORY_LABELS.get(k, k) for k in weak_areas[:2])}.",
        "days": plan,
    }


def _normalize_tasks(raw_tasks) -> list:
    """Accept either list[str] or list[dict] and return list[{title, detail}].

    Older LLM responses may emit plain strings; richer ones emit
    {"title": "...", "detail": "..."}. We always normalize to the object
    form so the UI can render both consistently.
    """
    out = []
    for t in raw_tasks or []:
        if isinstance(t, dict):
            title = (t.get("title") or t.get("task") or "").strip()
            detail = (t.get("detail") or t.get("description") or t.get("how") or "").strip()
            if not title and detail:
                # Promote detail to title if title is missing.
                title, detail = detail, ""
            if title:
                out.append({"title": title, "detail": detail})
        elif isinstance(t, str):
            s = t.strip()
            if s:
                out.append({"title": s, "detail": ""})
    return out


def generate_roadmap(report: dict, days: int) -> dict:
    """Build a day-by-day prep roadmap aligned with the user's weakest categories.

    Uses Groq Llama 3.3 70B (same model as the scoring pipeline). Falls back to a
    deterministic distributor if the key is missing or the call fails.
    """
    days = max(1, min(int(days or 1), 180))

    weak_keys = _rank_weaknesses(report) or ["answer_quality"]
    weak_summary = []
    cb = report.get("category_breakdown", {}) or {}
    for k in weak_keys[:4]:
        v = cb.get(k, {})
        weak_summary.append({
            "category": _CATEGORY_LABELS.get(k, k),
            "score": v.get("score"),
            "max": v.get("max"),
            "justification": v.get("justification", ""),
        })

    strengths = (report.get("strengths") or [])[:5]
    improvements = (report.get("areas_for_improvement") or [])[:5]
    exec_summary = report.get("executive_summary", "")

    if not os.environ.get("GROQ_API_KEY"):
        return _fallback_roadmap(report, days)

    system_prompt = (
        "You are a world-class interview coach (think ex-FAANG hiring manager) building "
        "a serious, personalized prep plan. This is NOT a generic to-do list — every "
        "task must feel hand-crafted for THIS candidate's specific weaknesses and "
        "strengths pulled from their interview report.\n\n"
        "HARD RULES:\n"
        "1. Produce EXACTLY the number of days requested.\n"
        "2. Each day has 2-4 tasks. Each task is a JSON object with:\n"
        "   - \"title\": 4-10 word action phrase, imperative verb first (e.g. "
        "'Record a 90-second STAR answer for system-design question').\n"
        "   - \"detail\": 25-55 words. Must include: the concrete step, HOW to do it "
        "(tool/technique/template), and a SUCCESS CRITERION (measurable outcome, "
        "timer, target count, or self-review check). Reference the candidate's actual "
        "weakness justification when possible.\n"
        "3. Each day ALSO has a \"focus_area\" (one of the category labels) and a "
        "realistic \"time_estimate_minutes\" (30-150, sum of all tasks that day).\n"
        "4. Rotate focus areas across days — weakest categories get more days, but no "
        "two consecutive days are identical. Never reuse the same title twice in the "
        "whole plan.\n"
        "5. Arc: Days 1-20% = diagnosis + foundational drills. Middle 60% = targeted "
        "skill reps + content creation. Final 20% = full mock interviews and polish.\n"
        "6. Tasks must be ACTIONABLE TODAY — not vague advice. Bad: 'Improve "
        "confidence'. Good: 'Record 3 takes of the Amazon Leadership Principles "
        "question; keep the one where your first sentence lands in under 8 seconds.'\n"
        "7. Ground in the report: cite the candidate's named weaknesses, strengths, "
        "or improvement areas at least once every 3 days.\n"
        "Return ONLY valid JSON matching the schema — no prose outside JSON."
    )

    schema_hint = (
        '{"primary_focus": "<category label>", '
        '"summary": "<2-3 sentences framing the plan, referencing the candidate\'s '
        'weakest categories by name and the overall arc>", '
        '"days": [{"day": <int starting at 1>, "focus_area": "<category label>", '
        '"tasks": [{"title": "<4-10 word imperative>", '
        '"detail": "<25-55 word how-to with success criterion>"}], '
        '"time_estimate_minutes": <int, 30-150>}]}'
    )

    few_shot_example = {
        "focus_area": "Answer Quality",
        "tasks": [
            {
                "title": "Draft 3 STAR answers for JD-critical bullets",
                "detail": "Pick the 3 highest-priority requirements from the job description. For each, write a 4-sentence STAR answer using a real project, ending with a quantified result. Success: each answer fits in under 90 spoken seconds when timed.",
            },
            {
                "title": "Rewrite your weakest past answer",
                "detail": "From your latest interview transcript, take the lowest-scoring answer. Rewrite it to lead with a 1-line direct answer, then 2-3 sentences of specific evidence. Success: second version is at least 20% shorter with higher specificity.",
            },
        ],
        "time_estimate_minutes": 90,
    }

    user_payload = {
        "days_requested": days,
        "weak_categories": weak_summary,
        "strengths": strengths,
        "areas_for_improvement": improvements,
        "executive_summary": exec_summary,
        "schema": schema_hint,
        "example_day": few_shot_example,
        "instruction": (
            f"Generate exactly {days} days. Every single task must match the quality "
            "and specificity of example_day. No generic one-liners. No 2-word tasks."
        ),
    }

    try:
        client = _get_groq_client()
        # Larger token budget because tasks are now full objects with detail strings.
        token_budget = max(3500, min(8000, 180 * days + 1200))
        response = client.chat.completions.create(
            model=_GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload)},
            ],
            temperature=0.5,
            max_tokens=token_budget,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content.strip())
        plan_days = data.get("days") or []
        if not plan_days:
            return _fallback_roadmap(report, days)

        # Clamp / pad to exactly `days` entries.
        if len(plan_days) > days:
            plan_days = plan_days[:days]
        elif len(plan_days) < days:
            extras = _fallback_roadmap(report, days)["days"][len(plan_days):]
            plan_days = plan_days + extras

        for i, d in enumerate(plan_days, start=1):
            d["day"] = i
            d["tasks"] = _normalize_tasks(d.get("tasks"))
            d.setdefault("focus_area", _CATEGORY_LABELS.get(weak_keys[0], weak_keys[0]))
            # If the model under-specified the time, estimate from task detail length.
            if not d.get("time_estimate_minutes"):
                words = sum(len((t.get("detail") or "").split()) + 5 for t in d["tasks"])
                d["time_estimate_minutes"] = max(30, min(150, 15 + words // 3))

        return {
            "primary_focus": data.get("primary_focus")
                or _CATEGORY_LABELS.get(weak_keys[0], weak_keys[0]),
            "summary": data.get("summary") or f"{days}-day personalized preparation plan.",
            "days": plan_days,
        }
    except Exception:
        return _fallback_roadmap(report, days)


# ── Coach Chat ───────────────────────────────────────────────────────────────

_COACH_SYSTEM_TEMPLATE = """You are "Max", the candidate's personal interview coach.
Every reply MUST be grounded in the interview report below. Never invent scores, \
quotes, projects, or companies not in the report.

=== CANDIDATE INTERVIEW REPORT ===
Total score: {total_score}/100  (grade: {grade})
Executive summary: {summary}

Category breakdown:
{breakdown}

Strengths observed:
{strengths}

Areas for improvement:
{improvements}
=== END REPORT ===

OUTPUT FORMAT — follow EXACTLY, no exceptions:
1. Reply is ONLY bullet points. Each bullet begins with "- " and is on its own line.
2. No greetings, no preambles, no closings, no headings, no emojis, no markdown bold.
3. NO SENTENCES OUTSIDE BULLETS. Do not write any intro line before the bullets.
4. Hard length budget (count words across ALL bullets combined):
     - Easy / factual question  -> 1-2 bullets, total <= 20 words.
     - Complex / advice question -> 2-4 bullets, total <= 40 words.
5. Each bullet is short, concrete, specific. Prefer verbs. No filler words.
6. If the report does not cover the topic, say so in one bullet, then one bullet \
pivoting to the user's weakest area.

EXAMPLES:

User: "what's my weakest area?"
Assistant:
- Answer Quality is your lowest: 22/40.
- Focus: direct answers, tied to the JD.

User: "how do I fix my filler words and improve confidence?"
Assistant:
- Filler rate: 6/min. Replace "um" with a 1s pause.
- Record 2-min daily drills; review playback.
- Slow pace; breathe before each answer.
- Tone score is low — project warmth, not volume.

User: "tell me about Docker"
Assistant:
- Report doesn't cover Docker skills.
- Closest gap: technical depth in Answer Quality — drill core concepts from the JD.
"""


def _format_breakdown(cb: dict) -> str:
    lines = []
    for key, val in (cb or {}).items():
        if not isinstance(val, dict):
            continue
        label = _CATEGORY_LABELS.get(key, key)
        score = val.get("score")
        mx = val.get("max")
        just = (val.get("justification") or "").strip().replace("\n", " ")
        lines.append(f"- {label}: {score}/{mx} — {just[:220]}")
    return "\n".join(lines) if lines else "- (no category breakdown available)"


def _format_list(items: list) -> str:
    items = items or []
    if not items:
        return "- (none noted)"
    return "\n".join(f"- {str(x).strip()}" for x in items[:8])


def coach_chat(report: dict, history: List[dict], message: str) -> str:
    """Generate one grounded coach reply for the user's latest message.

    `history` is a list of {role, content} dicts from the client (ephemeral).
    Uses the same Groq Llama model as the scoring pipeline.
    """
    if not os.environ.get("GROQ_API_KEY"):
        return (
            "I can't reach the coaching model right now — the GROQ_API_KEY is not "
            "configured on the server. Ask your admin to set it, then try again."
        )

    system_prompt = _COACH_SYSTEM_TEMPLATE.format(
        total_score=report.get("total_score", "?"),
        grade=report.get("grade", "?"),
        summary=(report.get("executive_summary") or "").strip() or "(not provided)",
        breakdown=_format_breakdown(report.get("category_breakdown", {})),
        strengths=_format_list(report.get("strengths")),
        improvements=_format_list(report.get("areas_for_improvement")),
    )

    messages = [{"role": "system", "content": system_prompt}]
    for turn in (history or [])[-12:]:  # keep last 12 turns max
        role = turn.get("role")
        content = (turn.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message.strip()})

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model=_GROQ_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=140,
        )
        raw = (response.choices[0].message.content or "").strip()
        return _enforce_bullet_format(raw, message)
    except Exception as e:
        return f"Coach is temporarily unavailable ({type(e).__name__}). Please try again in a moment."


_PREAMBLE_PATTERNS = (
    "sure thing",
    "sure!",
    "of course",
    "great question",
    "good question",
    "absolutely",
    "let me help",
    "here are",
    "here's",
    "based on your",
    "to answer",
    "i'd say",
    "i would say",
)


def _is_preamble(s: str) -> bool:
    low = s.lower().lstrip(" -*•·").strip()
    return any(low.startswith(p) for p in _PREAMBLE_PATTERNS)


def _drop_leading_preamble_sentence(line: str) -> str:
    """Drop every leading preamble sentence, keeping only substantive content."""
    import re
    for _ in range(4):  # handle chained preambles like "Sure! Here are tips:"
        if not line or not _is_preamble(line):
            return line
        parts = re.split(r"(?<=[.!?])\s+", line, maxsplit=1)
        if len(parts) == 2:
            line = parts[1].strip()
            continue
        # Whole line is just a preamble — drop it.
        return ""
    return line


def _enforce_bullet_format(text: str, user_message: str) -> str:
    """Post-process the model output so the UI always sees tight bullets.

    - Strips preambles, markdown headings, bold, and numeric lists.
    - Splits inline numbered lists ("1. X. 2. Y.") into separate bullets.
    - Enforces the word budget: <=20 words for easy, <=40 for complex.
    """
    import re

    if not text:
        return "- (no response)"

    # Detect complexity from the user's message (rough heuristic).
    word_count_q = len(user_message.split())
    low_q = user_message.lower()
    is_complex = (
        word_count_q >= 12
        or " and " in low_q
        or any(k in low_q for k in ("how", "why", "explain", "strategy", "plan", "improve", "fix"))
    )
    budget = 40 if is_complex else 20
    max_bullets = 4 if is_complex else 2

    cleaned = text.replace("\r", "").strip()
    # Strip markdown bold/italics/headings globally.
    cleaned = re.sub(r"\*\*|__|^#+\s*", "", cleaned, flags=re.MULTILINE)

    # If the model emitted inline numbered bullets like "1. X. 2. Y. 3. Z.",
    # split them into separate lines BEFORE the line-by-line pass.
    cleaned = re.sub(r"(?<!^)\s+(?=\d+[.)]\s)", "\n", cleaned)

    lines = [ln.strip() for ln in cleaned.split("\n")]
    bullets: List[str] = []
    for ln in lines:
        if not ln:
            continue
        # Strip common bullet prefixes.
        for prefix in ("- ", "* ", "• ", "· "):
            if ln.startswith(prefix):
                ln = ln[len(prefix):].strip()
                break
        # Numbered list "1. ", "2) ", etc.
        m = re.match(r"^\d+[.)]\s*", ln)
        if m:
            ln = ln[m.end():].strip()
        # Trailing colon headings like "Here are tips:" become empty after strip.
        ln = ln.rstrip(":").strip("*_ ").strip()
        # Drop preamble sentences (e.g. "Great question. Your weakest area is X"
        # keeps only the substantive second sentence).
        ln = _drop_leading_preamble_sentence(ln)
        if ln:
            bullets.append(ln)

    # If still just one bullet that's a long sentence soup, split by sentence.
    if len(bullets) <= 1 and bullets:
        parts = re.split(r"(?<=[.!?;])\s+", bullets[0])
        parts = [p.strip(" -*•·").rstrip(".") for p in parts if p.strip()]
        if len(parts) > 1:
            bullets = parts

    # Cap bullet count.
    bullets = bullets[:max_bullets]

    # Enforce word budget by trimming from the tail.
    def _words(bs: list) -> int:
        return sum(len(b.split()) for b in bs)

    while bullets and _words(bullets) > budget:
        last = bullets[-1].split()
        if len(last) <= 2:
            bullets.pop()
        else:
            bullets[-1] = " ".join(last[:-1])

    if not bullets:
        return "- (no response)"

    return "\n".join(f"- {b.rstrip('.').strip()}" for b in bullets)
