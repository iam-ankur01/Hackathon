# HireSight

AI-assisted interview evaluation with a React/Vite frontend, FastAPI backend,
Firestore persistence, Firebase Storage, and Groq transcription/scoring.

## Local development

### Backend

```powershell
cd backend
pip install -r requirements.txt
Copy-Item .env.example .env
# Fill in local values. USE_LOCAL_DB=true works without Firebase.
python run.py
```

The API runs at http://127.0.0.1:8000 and documentation is available at
http://127.0.0.1:8000/docs.

### Frontend

```powershell
cd Frontend
npm install
Copy-Item .env.example .env
npm run dev -- --host 127.0.0.1
```

The web app runs at http://127.0.0.1:5173.

## Verification

```powershell
cd Frontend
npm run lint
npm run build
npm run test:e2e

cd ../backend
python -m compileall -q app
```

## Deployment

The recommended deployment is Vercel for the frontend and a Docker-based
Render service for the backend, with Firestore and private Firebase Storage.
See [DEPLOYMENT.md](DEPLOYMENT.md) for the full checklist.

Never commit `.env` files or Firebase service-account JSON files.
