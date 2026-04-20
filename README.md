# HireSight

AI interview evaluator — React frontend + FastAPI backend.
#NOTE - IF GROQ API KEY AND FIREBASE API KEY IS NOT WORKING ...YOU HAVE TO CHANGE IT IN .ENV FILE (IN BACKEND AND AI FOLDER)
## Stack
- **Frontend:** React + Vite + Tailwind (`Frontend/`)
- **Backend:** FastAPI + Firebase + Groq LLM (`backend/`)

## Run locally

**Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd Frontend
npm install
npm run dev
```

Set `VITE_API_URL` in `Frontend/.env` to your backend URL (default `http://localhost:8000`).

## Deploy

**Backend → Render**
- New Web Service → repo root `backend/`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Env vars: `FIREBASE_CREDENTIALS_JSON`, `GROQ_API_KEY`, `JWT_SECRET`, `ALLOWED_ORIGIN`

**Frontend → Vercel**
- Import repo → root `Frontend/`
- Framework: Vite (auto-detected)
- Env var: `VITE_API_URL=https://<your-backend>.onrender.com`

Update FastAPI CORS `allow_origins` to include the Vercel URL.
