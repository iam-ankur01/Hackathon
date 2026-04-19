FROM python:3.11-slim

# ffmpeg is required by the AI pipeline to chunk/convert non-MP3 audio and
# extract audio from video uploads (MP4/MOV/WebM). The other apt packages are
# minimal compile deps for bcrypt / cryptography on slim base images.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ffmpeg \
      build-essential \
      curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first so Docker can cache this layer.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source + AI pipeline (ai_service.py imports from ../AI).
COPY backend/ ./backend/
COPY AI/ ./AI/

WORKDIR /app/backend

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

EXPOSE 8000

# Render injects $PORT at runtime; fall back to 8000 locally.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
