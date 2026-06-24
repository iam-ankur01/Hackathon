"""FastAPI app entrypoint."""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .firebase import init_firebase
from .routes import auth, users, interviews, jobs, progress, history

app = FastAPI(
    title="Interview Evaluator API",
    description="Backend for the AI-powered interview coach.",
    version="1.0.0",
)

# FRONTEND_ORIGIN can be a single URL or a comma-separated list, so one deployed
# backend can serve both the production Vercel domain and preview deployments.
_origins = [o.strip() for o in (settings.FRONTEND_ORIGIN or "").split(",") if o.strip()]
if not settings.is_production and "http://localhost:3000" not in _origins:
    _origins.append("http://localhost:3000")

_origin_regex = None if settings.is_production else r"^http://(?:localhost|127\.0\.0\.1):\d+$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    settings.validate_production()
    try:
        init_firebase()
        print("[startup] Firebase initialized.")
    except Exception as e:
        print(f"[startup] Firebase init failed: {e}")
        if settings.is_production:
            raise


@app.get("/")
def root():
    return {"service": "interview-evaluator", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/ready")
def ready():
    from .firebase import get_db

    list(get_db().collection("_health").limit(1).stream())
    return {"status": "ready"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(interviews.router)
app.include_router(jobs.router)
app.include_router(progress.router)
app.include_router(history.router)
