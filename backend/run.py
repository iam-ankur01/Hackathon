"""Dev entrypoint: python run.py"""
import sys

# Force UTF-8 stdout on Windows so the AI pipeline's ═ ✅ ⚠ prints don't crash
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
