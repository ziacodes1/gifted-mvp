# Gifted MVP

Student-first platform to discover, explore, validate and develop potential.
Modular monolith: Django + DRF + PostgreSQL backend, React + TS + Vite frontend.

> Backend runs on **port 8001** (8000 is used by another local project).

## Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# PostgreSQL (local): assumes a running server and a database named `gifted_mvp`.
# Create it once if needed:  createdb gifted_mvp
# Config is read from backend/.env (copy from .env.example and adjust user/password).

python manage.py migrate
python manage.py seed_demo          # demo student/parent/admin @gifted.demo (pw: demo123)
python manage.py createsuperuser    # optional, for Django admin
python manage.py runserver 127.0.0.1:8001
```

API base: `http://127.0.0.1:8001/api/v1/` — `health/`, `auth/register|login|refresh|me/`, `assessments/`, `assessment-sessions/{id}/{,answer,complete}/`, `signals/me/`.

## Frontend

```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

`frontend/.env` sets `VITE_API_URL` (defaults to the backend on 8001).

## Demo accounts (after `seed_demo`)

| Role    | Email               | Password |
| ------- | ------------------- | -------- |
| Student | student@gifted.demo | demo123  |
| Parent  | parent@gifted.demo  | demo123  |
| Admin   | admin@gifted.demo   | demo123  |

Demo loop: log in as the student → Dashboard → Start Assessment → answer the 7 "Interests
Discovery" questions → Complete → Emerging Profile.

See `PROJECT_STATE.md` for architecture and current status.
