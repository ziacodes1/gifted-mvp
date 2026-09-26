# Gifted

Youth potential discovery platform: **Assessment → deterministic signals → AI interpretation →
Gifted Passport → missions & evidence → AI Companion, diary and daily guidance.**
AI interprets; it never scores.

Stage: controlled-pilot **POC foundation** (not production) — see `POC_READINESS.md`.

| Doc | What |
|---|---|
| `ARCHITECTURE.md` | modular monolith, domains, diagram, privacy boundaries |
| `ASSESSMENT_METHOD.md` | scoring, confidence, versioning, limitations, validation plan |
| `PRIVACY.md` | private vs parent-safe data, deletion, retention, backups |
| `DEPLOYMENT.md` | local, Docker, POC hosting, configuration |
| `POC_READINESS.md` | what is real, hardcoding audit, hardening, what remains |
| `DEMO.md` | demo commands and presentation flow |
| `PROJECT_STATE.md` | detailed milestone log |

## Quick start (local)

```bash
# Backend (PostgreSQL running locally)
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                    # DJANGO_ENV=development; adjust POSTGRES_*, secret
createdb gifted_mvp
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo    # demo content + demo accounts (demo only)
.venv/bin/python manage.py runserver 127.0.0.1:8001

# Frontend
cd frontend && npm ci && npm run dev    # http://localhost:5173
```

- API: `http://127.0.0.1:8001/api/v1/` · docs: `/api/v1/docs/` · health: `/api/v1/health/live/`, `/api/v1/health/ready/`
- Django admin (content, rewards, fulfilment): `http://127.0.0.1:8001/admin/`
- Full stack in Docker: `docker compose up --build` (see `DEPLOYMENT.md`)

## Demo accounts (after `seed_demo`, demo only)

| Role | Email | Password |
|---|---|---|
| Student | student@gifted.demo | demo123 |
| Parent | parent@gifted.demo | demo123 |
| Admin (Django admin) | admin@gifted.demo | demo123 |

Demo passwords are set by the seed and bypass the password policy (min 10 chars) that applies to
real registrations. Never run the seed commands against a pilot database.

## Checks (same as CI)

```bash
cd backend && .venv/bin/python manage.py check && .venv/bin/python manage.py makemigrations --check --dry-run && .venv/bin/python manage.py test
cd frontend && npm test && npx tsc -b && npm run lint && npm run build
```
