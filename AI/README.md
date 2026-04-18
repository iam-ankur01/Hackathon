# AI Interview Evaluator

AI-powered interview performance evaluation system. Scores candidates out of 100 using a structured rubric with speaker diarization, profile cross-verification, and detailed feedback.

## Scoring Rubric (100 Points)

| Category | Points | What's Evaluated |
|----------|--------|------------------|
| 🎤 Public Speaking | 30 | Clarity, tone, confidence, articulation |
| ✅ Answer Quality | 40 | Correctness, relevance to questions & job description |
| 🔍 Consistency | 20 | Cross-verified against resume, GitHub, LinkedIn |
| 🗣️ Filler Words | 10 | "um", "uh", "like" — candidate-only analysis |

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your Groq API key to .env
echo "GROQ_API_KEY=your_key_here" > .env

# 3. (Optional) Install ffmpeg for audio/video support
# Mac:   brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

## Usage

### Option 1 — Python Import

```python
from pipeline_v2 import evaluate_interview

report = evaluate_interview(
    # Session data (per evaluation)
    interview_path="interview.mp3",
    job_description="Software Engineer at Google. Python, ML, 3+ years...",
    
    # Profile data (from signup)
    resume_path="resume.pdf",
    github_url="johndoe",
    linkedin_url="johndoe",
)

report.print_report()         # beautiful terminal output
print(report.to_json())       # structured JSON
print(report.total_score)     # 0–100
print(report.grade)           # A+ to F
```

### Option 2 — Command Line

```bash
# Basic evaluation
python pipeline_v2.py interview.mp3

# Full evaluation with all inputs
python pipeline_v2.py interview.mp3 \
  --jd "Software Engineer at Google..." \
  --resume resume.pdf \
  --github johndoe \
  --linkedin johndoe

# Evaluate a JSON transcript
python pipeline_v2.py transcript.json --jd "Data Scientist role..."

# Save JSON output
python pipeline_v2.py interview.mp3 --json-output report.json
```

### Option 3 — Quick Script

```bash
# Edit run.py with your paths, then:
python run.py
```

## Inputs

### Profile Data (from signup/profile edit)
| Input | Format | Required |
|-------|--------|----------|
| Resume | PDF, DOCX | Optional |
| GitHub | URL or username | Optional |
| LinkedIn | URL or ID | Optional |

### Session Data (per evaluation)
| Input | Format | Required |
|-------|--------|----------|
| Job Description | Text (title + role + company) | Recommended |
| Interview Content | MP3, MP4, WAV, JSON, TXT | **Required** |

## Output Example

```json
{
  "total_score": 72.0,
  "grade": "B-",
  "category_breakdown": {
    "public_speaking": {
      "score": 22.0,
      "max": 30,
      "justification": "Clear articulation with confident tone...",
      "sub_scores": {
        "Clarity (0-8)": 6,
        "Tone (0-8)": 6,
        "Confidence (0-8)": 5,
        "Articulation (0-6)": 5
      }
    },
    "answer_quality": {
      "score": 30.0,
      "max": 40,
      "justification": "Technically accurate answers...",
      "sub_scores": {
        "Technical Correctness (0-15)": 12,
        "Question Relevance (0-13)": 10,
        "JD Relevance (0-12)": 8
      }
    },
    "consistency_truthfulness": {
      "score": 14.0,
      "max": 20,
      "justification": "Claims mostly consistent with resume..."
    },
    "filler_word_assessment": {
      "score": 6.0,
      "max": 10,
      "justification": "4.2 fillers/min — acceptable but improvable"
    }
  },
  "strengths": ["Strong technical depth", "Clear communication"],
  "areas_for_improvement": ["Reduce filler words", "Better STAR structure"],
  "executive_summary": "..."
}
```

## Architecture

```
interview_evaluator/
├── .env                  ← Groq API key
├── requirements.txt      ← pip dependencies
├── pipeline_v2.py        ← master pipeline (run this)
├── transcriber.py        ← Groq Whisper STT (chunked for long audio)
├── speaker_diarizer.py   ← AI speaker role identification
├── rule_engine.py        ← filler/pause/WPM (pure Python, no API)
├── evaluator.py          ← Groq Llama quality scoring
├── feedback.py           ← Groq Llama debrief generation
├── profile_parser.py     ← resume/GitHub/LinkedIn extraction
├── interview_scorer.py   ← 100-point rubric scoring engine
└── run.py                ← quick-start script
```

## Pipeline Flow

```
1. PROFILE PARSING
   Resume (PDF/DOCX) → structured skills/experience
   GitHub (API)      → repos, languages, contributions
   LinkedIn          → experience, skills, education
   ↓ synthesize into unified CandidateProfile

2. TRANSCRIPTION
   Audio/Video → Groq Whisper → raw transcript + word timestamps

3. SPEAKER DIARIZATION
   Raw transcript → Llama 3.3 → interviewer vs candidate separation
   (uses question/answer patterns, conversational flow, context)

4. RULE ENGINE (candidate speech only)
   Filler detection, pause analysis, WPM, vocabulary richness

5. SCORING (100-point rubric)
   30 pts: Public Speaking → Llama 3.3 analysis
   40 pts: Answer Quality  → Llama 3.3 + JD matching
   20 pts: Consistency     → Llama 3.3 + profile cross-verification
   10 pts: Filler Words    → rule-based (instant)
```

## Supported Formats
- **Audio**: MP3, WAV, M4A, OGG, WEBM
- **Video**: MP4 (audio extracted via ffmpeg)
- **Transcript**: JSON, TXT
- **Resume**: PDF, DOCX, TXT

## Cost
**₹0** — Groq free tier covers ~12,000 min/month Whisper + unlimited Llama 3.3 calls.
