"""Dev entrypoint: python run.py"""
import os
import socket
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HOST = "0.0.0.0"
PORT = 8000


def _port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True


def _port_owner_pid(port: int) -> str:
    if os.name != "nt":
        return ""
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | "
             f"Select-Object -First 1).OwningProcess"],
            text=True, stderr=subprocess.DEVNULL, timeout=3,
        ).strip()
        return out
    except Exception:
        return ""


def _log_groq_key() -> None:
    from dotenv import load_dotenv
    load_dotenv()
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        print("[run.py] GROQ_API_KEY: MISSING (pipeline calls will fail)",
              file=sys.stderr, flush=True)
        return
    print(f"[run.py] GROQ_API_KEY loaded: {key[:8]}...{key[-4:]}",
          file=sys.stderr, flush=True)


if __name__ == "__main__":
    if _port_in_use(HOST, PORT):
        pid = _port_owner_pid(PORT)
        owner = f" (PID {pid})" if pid else ""
        print(
            f"[run.py] ERROR: port {PORT} is already in use{owner}.\n"
            f"         A previous backend is still running. Kill it first:\n"
            f"           powershell -NoProfile -Command \"Stop-Process -Id {pid or '<PID>'} -Force\"\n"
            f"         Then rerun `python run.py`.",
            file=sys.stderr,
        )
        sys.exit(1)

    _log_groq_key()

    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
