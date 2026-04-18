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
from .routes import auth, users, interviews, jobs, progress

app = FastAPI(
    title="Interview Evaluator API",
    description="Backend for the AI-powered interview coach.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    try:
        init_firebase()
        print("[startup] Firebase initialized.")
    except Exception as e:
        print(f"[startup] Firebase init failed: {e}")


@app.get("/")
def root():
    return {"service": "interview-evaluator", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(interviews.router)
app.include_router(jobs.router)
app.include_router(progress.router)
