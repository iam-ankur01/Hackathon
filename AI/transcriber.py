"""
transcriber.py
Groq Whisper — smart chunking for long audio/video.

Strategy:
  - < 10 min   → direct transcription (single call)
  - 10–60 min  → 8-min chunks, 15s overlap, sequential
  - > 60 min   → 8-min chunks, 15s overlap, parallel (ThreadPoolExecutor)
"""

import os
import math
import shutil
import struct
import subprocess
import tempfile
import concurrent.futures
from dataclasses import dataclass
from typing import List, Dict, Tuple
from groq import Groq

# Check if ffmpeg/ffprobe are available on PATH
HAS_FFMPEG = shutil.which("ffmpeg") is not None
HAS_FFPROBE = shutil.which("ffprobe") is not None

# ── Constants ──────────────────────────────────────────────────────────────────
CHUNK_DURATION     = 8 * 60     # 8 min per chunk (seconds)
OVERLAP_DURATION   = 15         # 15s overlap at chunk boundaries
SHORT_THRESHOLD    = 10 * 60    # < 10 min → no chunking needed
PARALLEL_THRESHOLD = 60 * 60    # > 60 min → use parallel workers
MAX_WORKERS        = 4          # max concurrent Groq API calls


@dataclass
class TranscriptResult:
    text: str
    word_timestamps: List[Dict]   # [{word, start, end}, ...]
    duration_seconds: float
    language: str
    chunk_count: int


# ── Audio utilities ────────────────────────────────────────────────────────────

def _get_duration_python(path: str) -> float:
    """Pure-Python MP3 duration estimation (no ffprobe needed)."""
    # Try mutagen first (most accurate)
    try:
        from mutagen.mp3 import MP3
        audio = MP3(path)
        return audio.info.length
    except ImportError:
        pass
    except Exception:
        pass

    # Try mutagen generic
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(path)
        if audio and audio.info:
            return audio.info.length
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: estimate from file size for MP3 (assuming ~128kbps)
    ext = os.path.splitext(path)[1].lower()
    if ext == ".mp3":
        size_bytes = os.path.getsize(path)
        # 128 kbps = 16000 bytes/sec
        estimated = size_bytes / 16000.0
        print(f"  [transcriber] ⚠ Estimating duration from file size: ~{estimated:.0f}s")
        return estimated

    return 0.0


def _get_duration(path: str) -> float:
    """Get audio duration. Uses ffprobe if available, else pure-Python fallback."""
    if HAS_FFPROBE:
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                path
            ]
            r = subprocess.run(cmd, capture_output=True, text=True)
            val = float(r.stdout.strip())
            if val > 0:
                return val
        except (ValueError, FileNotFoundError, OSError):
            pass

    # Pure-Python fallback
    return _get_duration_python(path)


def _extract_segment(src: str, start: float, dur: float, dst: str):
    if not HAS_FFMPEG:
        raise RuntimeError(
            "ffmpeg is required for long audio chunking. "
            "Install it: brew install ffmpeg (Mac) / sudo apt install ffmpeg (Linux)"
        )
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(round(start, 3)),
        "-t",  str(round(dur,   3)),
        "-i", src,
        "-ar", "16000", "-ac", "1", "-q:a", "2",
        dst, "-loglevel", "error"
    ]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {r.stderr.decode()}")


def _to_mono_mp3(path: str) -> Tuple[str, bool]:
    """Returns (converted_path, is_temp). Caller deletes if is_temp."""
    ext = os.path.splitext(path)[1].lower()
    size_mb = os.path.getsize(path) / (1024 * 1024)

    # Small MP3 files can be sent directly — no conversion needed
    if ext == ".mp3" and size_mb < 24:
        return path, False

    # For non-MP3 or large files, we need ffmpeg
    if not HAS_FFMPEG:
        if ext in (".mp3", ".wav", ".m4a", ".ogg", ".webm") and size_mb < 24:
            # Groq Whisper accepts these formats directly under 25MB
            print(f"  [transcriber] ⚠ No ffmpeg — sending {ext} directly to Whisper")
            return path, False
        raise RuntimeError(
            f"ffmpeg is required to convert {ext} files or files >24MB. "
            "Install it: brew install ffmpeg (Mac) / sudo apt install ffmpeg (Linux)"
        )

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    cmd = [
        "ffmpeg", "-y", "-i", path,
        "-ar", "16000", "-ac", "1", "-q:a", "2",
        tmp.name, "-loglevel", "error"
    ]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg convert failed: {r.stderr.decode()}")
    return tmp.name, True


# ── Single chunk transcription ─────────────────────────────────────────────────

def _transcribe_chunk(audio_path: str, language: str,
                      time_offset: float,
                      chunk_index: int, total_chunks: int) -> List[Dict]:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    label  = f"chunk {chunk_index+1}/{total_chunks}" if total_chunks > 1 else "full audio"
    print(f"  [whisper] {label}  offset={time_offset/60:.1f}min ...")

    with open(audio_path, "rb") as f:
        resp = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), f),
            model="whisper-large-v3",
            language=language,
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )

    words = []
    for w in (resp.words or []):
        if isinstance(w, dict):
            word, start, end = w.get("word","").strip(), w.get("start",0), w.get("end",0)
        else:
            word, start, end = w.word.strip(), w.start, w.end
        if not word:
            continue
        words.append({
            "word":  word,
            "start": round(float(start) + time_offset, 3),
            "end":   round(float(end)   + time_offset, 3),
        })
    return words


# ── Chunk plan ─────────────────────────────────────────────────────────────────

def _build_chunk_plan(duration: float) -> List[Dict]:
    """
    Each chunk:
      extract_start = logical_start - OVERLAP  (gives Whisper context)
      extract_dur   = CHUNK_DURATION + OVERLAP
      time_offset   = extract_start  (so returned timestamps are global)
    We only KEEP words whose start >= logical_start (skip overlap head).
    """
    chunks = []
    t = 0.0
    while t < duration:
        logical_start  = t
        logical_end    = min(t + CHUNK_DURATION, duration)
        extract_start  = max(0.0, t - OVERLAP_DURATION)
        extract_dur    = min(CHUNK_DURATION + OVERLAP_DURATION * 2,
                             duration - extract_start)
        chunks.append({
            "logical_start": logical_start,
            "logical_end":   logical_end,
            "extract_start": extract_start,
            "extract_dur":   extract_dur,
        })
        t = logical_end
    return chunks


# ── Merge with overlap dedup ───────────────────────────────────────────────────

def _merge(all_words: List[List[Dict]], chunk_plan: List[Dict]) -> List[Dict]:
    """
    For each chunk, only accept words whose global start >= logical_start.
    This discards overlap-head words that are duplicates from prev chunk.
    Then do a final pass to remove any consecutive near-duplicate words.
    """
    merged = []
    for i, words in enumerate(all_words):
        if not words:
            continue
        keep_from = chunk_plan[i]["logical_start"]
        for w in words:
            if w["start"] >= keep_from - 0.3:   # 300ms grace
                merged.append(w)

    merged.sort(key=lambda w: w["start"])

    # Remove consecutive duplicates within 2s window (overlap edge cases)
    clean = []
    for w in merged:
        if (clean and
                clean[-1]["word"].lower() == w["word"].lower() and
                abs(w["start"] - clean[-1]["start"]) < 2.0):
            continue
        clean.append(w)
    return clean


# ── Public API ─────────────────────────────────────────────────────────────────

def transcribe(audio_path: str, language: str = "en") -> TranscriptResult:
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Not found: {audio_path}")

    print(f"\n[transcriber] File : {audio_path}")

    if not HAS_FFPROBE:
        print("  [transcriber] ⚠ ffprobe not found — using Python fallback for duration")

    duration = _get_duration(audio_path)
    if duration <= 0:
        # Try converting first, then re-check duration
        try:
            p, t = _to_mono_mp3(audio_path)
            duration = _get_duration(p)
            if t and os.path.exists(p): os.unlink(p)
        except RuntimeError:
            # If conversion fails too, estimate from file size
            duration = _get_duration_python(audio_path)

    # If still zero, use a safe default for short files
    if duration <= 0:
        size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        duration = size_mb * 60  # rough: ~1MB per minute at 128kbps
        print(f"  [transcriber] ⚠ Could not determine duration, estimating ~{duration:.0f}s")

    mins = duration / 60
    print(f"[transcriber] Duration : {mins:.1f} min", end="  |  ")

    # ── Short: single call ────────────────────────────────────────────────────
    if duration <= SHORT_THRESHOLD:
        print("mode=direct")
        p, is_tmp = _to_mono_mp3(audio_path)
        try:
            words = _transcribe_chunk(p, language, 0.0, 0, 1)
        finally:
            if is_tmp and os.path.exists(p): os.unlink(p)

        text     = " ".join(w["word"] for w in words)
        end_time = words[-1]["end"] if words else duration
        print(f"[transcriber] Done — {len(words)} words | {end_time:.1f}s")
        return TranscriptResult(text, words, end_time, language, 1)

    # ── Long: chunked ─────────────────────────────────────────────────────────
    plan      = _build_chunk_plan(duration)
    n         = len(plan)
    parallel  = duration > PARALLEL_THRESHOLD
    print(f"mode={'parallel' if parallel else 'sequential'} | {n} chunks × {CHUNK_DURATION//60}min | overlap={OVERLAP_DURATION}s")

    # Extract segments
    tmp_dir = tempfile.mkdtemp(prefix="antigravity_")
    seg_paths = []
    print(f"[transcriber] Extracting {n} segments...")
    for i, c in enumerate(plan):
        dst = os.path.join(tmp_dir, f"seg_{i:03d}.mp3")
        _extract_segment(audio_path, c["extract_start"], c["extract_dur"], dst)
        seg_paths.append(dst)

    # Transcribe
    all_words: List[List[Dict]] = [None] * n

    def _job(i):
        c = plan[i]
        return i, _transcribe_chunk(
            seg_paths[i], language,
            time_offset=c["extract_start"],
            chunk_index=i, total_chunks=n
        )

    if parallel:
        print(f"[transcriber] Parallel workers={MAX_WORKERS} ...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futs = {ex.submit(_job, i): i for i in range(n)}
            for fut in concurrent.futures.as_completed(futs):
                idx, w = fut.result()
                all_words[idx] = w
    else:
        for i in range(n):
            _, w = _job(i)
            all_words[i] = w

    # Cleanup segments
    for p in seg_paths:
        if os.path.exists(p): os.unlink(p)
    try: os.rmdir(tmp_dir)
    except: pass

    # Merge
    print(f"[transcriber] Merging {n} chunks...")
    merged   = _merge([w for w in all_words if w], plan)
    text     = " ".join(w["word"] for w in merged)
    end_time = merged[-1]["end"] if merged else duration

    print(f"[transcriber] Done — {len(merged)} words | {n} chunks | {end_time/60:.1f} min")
    return TranscriptResult(text, merged, end_time, language, n)
