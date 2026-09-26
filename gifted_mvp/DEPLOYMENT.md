# Gifted — Deployment (controlled-pilot POC)

Shape: **nginx (SPA + proxy) → Django API (gunicorn) → PostgreSQL**; AI providers external;
private diary photos on a private volume or an S3-compatible bucket.

## 1. Local development (no Docker)

```bash
# backend
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env            # DJANGO_ENV=development; set POSTGRES_* and a DJANGO_SECRET_KEY
createdb gifted_mvp
.venv/bin/python manage.py migrate && .venv/bin/python manage.py seed_demo
.venv/bin/python manage.py runserver 127.0.0.1:8001
# frontend
cd frontend && npm ci && npm run dev      # http://localhost:5173
```

## 2. Full stack with Docker (reproducible)

```bash
cp .env.docker.example .env.docker        # set DJANGO_SECRET_KEY (≥ 50 chars), optional AI keys
docker compose up --build                  # http://localhost:8080 · admin: /admin/ · docs: /api/v1/docs/
docker compose exec backend python manage.py seed_demo          # optional demo content
docker compose exec backend python manage.py createsuperuser    # staff account for Django admin
```

The backend image runs `migrate` and `collectstatic` on start (`RUN_MIGRATIONS=0` to skip) and then
gunicorn as a non-root user. The compose file is for local/plain-HTTP use (it disables HTTPS
redirects and secure cookies via `.env.docker`); remove those overrides behind HTTPS.

> Docker was not available on the machine where these files were written: the images and compose
> file are syntax-checked but not yet built/run. The same production path was verified without
> Docker (gunicorn + `DJANGO_ENV=production` + whitenoise + health probes).

## 3. POC hosting (one reasonable option)

Any platform that runs two containers and a managed PostgreSQL works (e.g. a small VM with Docker
Compose, Render, Railway, Fly.io, a cloud container service):

1. Managed PostgreSQL with automated backups (see `PRIVACY.md` §5).
2. Backend container: `DJANGO_ENV=production`, strong `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`,
   `CSRF_TRUSTED_ORIGINS`, `POSTGRES_*`, `AI_PROVIDER` + key, `LOG_FORMAT=json`, optional `SENTRY_DSN`.
3. Frontend container (nginx) built with `VITE_API_URL=/api/v1` and `VITE_DEMO_MODE=false`.
4. TLS at the platform/load balancer, forwarding `X-Forwarded-Proto` (Django then enforces HTTPS,
   secure cookies and HSTS).
5. Private storage: `PRIVATE_STORAGE_BACKEND=s3` + `PRIVATE_S3_*` (private bucket, versioning on);
   build the backend with `--build-arg WITH_OPTIONAL=1`.
6. Probes: liveness `/api/v1/health/live/`, readiness `/api/v1/health/ready/` (DB only — AI outages
   never make the app unready, because every AI feature has a fallback).

Production **fails closed**: with `DJANGO_ENV=production` the process refuses to start if the secret
is missing/weak/default, `DEBUG` is true, or hosts are empty/`*` (`config/security.py`, tested).

## 4. Configuration reference

See `backend/.env.example` (all variables, development defaults) and `.env.docker.example`.
Key groups: environment/security, database, JWT/password policy, throttling rates, AI provider,
private storage, logging/Sentry, API docs toggle.

## 5. Scaling notes (not needed for a pilot)

- Throttle counters use an in-process cache: exact per worker. With several workers/instances,
  configure a shared cache (Django DB cache or Redis) — that is the first reason to add Redis.
- AI calls are synchronous with short timeouts and fallbacks; move to a task queue only if usage
  shows long tail latencies.
