# Interview Evaluator — Backend

FastAPI backend that wraps the AI interview-evaluation pipeline and stores users,
profiles, and scored reports in **Firebase Firestore**.

## Quick start

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # win: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env → fill in GROQ_API_KEY and FIREBASE_CREDENTIALS path

# Put your Firebase service-account JSON at the path from FIREBASE_CREDENTIALS
# (download from Firebase Console → Project Settings → Service Accounts → Generate Key)

python run.py
# API at http://localhost:8000, docs at http://localhost:8000/docs
```

## Endpoints

| Method | Path                          | Description                                  |
|--------|-------------------------------|----------------------------------------------|
| POST   | `/api/auth/signup`            | Create user, returns JWT                     |
| POST   | `/api/auth/login`             | Login, returns JWT                           |
| GET    | `/api/auth/me`                | Current user                                 |
| GET    | `/api/users/me`               | Get profile                                  |
| PATCH  | `/api/users/me`               | Update profile                               |
| POST   | `/api/users/me/resume`        | Upload resume (PDF/DOCX)                     |
| POST   | `/api/interviews/`            | Submit interview audio/transcript (async)    |
| GET    | `/api/interviews/`            | List my interviews                           |
| GET    | `/api/interviews/{id}`        | Fetch full scoring report                    |
| DELETE | `/api/interviews/{id}`        | Delete an interview                          |
| GET    | `/api/dashboard`              | Dashboard summary                            |
| GET    | `/api/progress`               | Score-over-time + category averages          |
| GET    | `/api/jobs`                   | Job matches (scored vs. user's skills)       |
| GET    | `/api/roadmap?days=N`         | Personalized N-day prep roadmap (1–180)      |
| POST   | `/api/roadmap/preferences`    | Save preferred roadmap duration              |
| GET    | `/api/coach`                  | Coaching tips from latest interview          |
| POST   | `/api/coach/chat`             | Grounded chat with the AI coach (Groq Llama) |

All authenticated endpoints require `Authorization: Bearer <token>`.

## Analysis flow (Groq-powered)

When a user uploads a video/audio file, the pipeline runs in two phases:

1. **Transcription (Groq Whisper `whisper-large-v3`)** — `AI/transcriber.py`
   converts the media to text with word-level timestamps.
2. **Analysis (Groq Llama `llama-3.3-70b-versatile`)** — `AI/speaker_diarizer.py`
   and `AI/interview_scorer.py` split speakers, score the interview on a
   100-point rubric, and emit structured insights.

The same Groq Llama model also powers the dynamic roadmap generator
(`/api/roadmap`) and the AI Coach chat (`/api/coach/chat`), both grounded
strictly in the latest interview report.

## Firestore collections

- `users/{userId}` — auth + profile fields
- `interviews/{interviewId}` — one doc per submission, `user_id` field scopes access
- `jobs/{jobId}` — optional; falls back to seeded in-memory list if empty

## Architecture

```
backend/
├── app/
│   ├── main.py            # FastAPI app, CORS, router mount
│   ├── config.py          # .env-driven Settings
│   ├── firebase.py        # firebase-admin init + helpers
│   ├── security.py        # bcrypt + JWT + get_current_user dep
│   ├── schemas.py         # Pydantic models
│   ├── routes/
│   │   ├── auth.py        # signup/login/me
│   │   ├── users.py       # profile + resume upload
│   │   ├── interviews.py  # submit + list + report
│   │   ├── jobs.py        # job matches, roadmap, coach
│   │   └── progress.py    # dashboard + progress
│   └── services/
│       └── ai_service.py  # wraps ../AI/pipeline_v2.py
├── requirements.txt
├── run.py
└── .env.example
```

The `AI/` folder is added to `sys.path` at runtime so `pipeline_v2` runs in-process.
