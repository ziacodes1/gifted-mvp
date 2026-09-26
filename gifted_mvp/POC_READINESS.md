# Gifted — POC Readiness Report

**Stage:** Hackathon MVP → **Controlled-pilot POC foundation** (this milestone) → Production platform (future).
Gifted is **not production-ready**. This report lists what is real, what was hardened, and what remains.

## 1. Current tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, Axios, i18next (EN/UZ/RU), Vitest |
| Backend | Python 3.13, Django 5.2, Django REST Framework, SimpleJWT (+ token blacklist), Pydantic, Pillow, drf-spectacular, gunicorn, whitenoise |
| Data | PostgreSQL 16 |
| AI | provider abstraction: Groq (primary, `openai/gpt-oss-20b`), Gemini, Anthropic, stub; deterministic fallbacks |
| Delivery | Dockerfiles (API, nginx SPA), docker-compose, GitHub Actions CI |

## 2. What is real / dynamic

- Assessment V2 (10 items, 6 formats) served from the database; deterministic scoring; per-session
  version + frozen results.
- AI Emerging Profile, Parent Insight, AI Companion — live provider calls with validation, persisted
  insights (one per session/version/language) and fallbacks.
- Gifted Passport (EMPTY → EMERGING → GROWING), missions with rule-based evidence, parent mode.
- My Diary (text, mood, tags, stickers, photos), Companion → Diary opt-in.
- Streaks, points, badges, weekly leaderboard, rewards + redemption, Today's Spark, in-app nudges.
- EN/UZ/RU UI, localized server content and AI output.
- Ecosystem: partner organizations, resources + learning paths (bookmark, progress, opt-in
  evidence), opportunities (filters, eligibility, save / view / application-link-opened), moderated
  community circles, posts, reports and events — all matched to the Passport deterministically.

## 3. What is still configured in code (and why) — hardcoding audit

Class: **A** should be admin-managed · **B** should stay versioned code/config · **C** demo-only · **D** environment configuration.

| Item | Current source | Why | POC action | Class | Status |
|---|---|---|---|---|---|
| Assessment items & options | DB (default content seeded from `seed_demo_assessment.py`) | content changes often | Django admin with inlines; locked once used; new draft version + publish | A | ✅ done |
| Option → signal mappings & weights | DB `ResponseSignalMap` | these are the scoring rules for content | admin (option page inline + table), locked once used | A | ✅ done |
| Signal catalogue (labels, translations) | DB `Signal` | labels are content | admin; **keys** stay stable (referenced by code/prompts) | A/B | ✅ done |
| Scoring formula & confidence thresholds | `assessments/services/scoring.py` | determinism + auditability; must not change silently | versioned by `SCORING_VERSION`, recorded per session | B | ✅ versioned |
| Mission definitions & steps | DB (seeded from `seed_demo_mission.py`) | content | admin (steps inline) | A | ✅ done |
| Mission evidence rules/weights | DB `MissionSignalMap` | evidence semantics | admin inline; evidence is frozen at completion | A | ✅ done |
| Featured mission selection | code (`missions.services.featured_mission`) | only one mission exists | becomes admin field when missions > 1 | A | ⏳ later |
| Points, caps, streak bonus | `engagement/rules.py` | anti-grinding logic must be deliberate | one config file, reviewed changes | B | ✅ centralized |
| Badge conditions | `engagement/rules.py` (+ copy in locales) | conditions are logic | stays code; titles translatable | B | ✅ |
| Rewards catalog | DB `Reward` | business content | admin (costs, stock, availability) + fulfilment queue | A | ✅ done |
| Reward artwork | frontend assets by `image_key` | bundled images | upload via admin later | B→A | ⏳ later |
| Today's Spark catalogue & weights | `today/catalog.py` + locale copy | product logic + translated copy | stays code for the POC | B | ✅ |
| Curated facts | frontend locale JSON | translated copy | translators edit JSON | B | ✅ |
| Diary page target (100), photo limits | `diary/services.py` | product constants | stays code | B | ✅ |
| AI prompts, banned phrases, schemas | `ai/prompts`, `ai/services`, `ai/schemas` | safety-critical; must be reviewed | versioned (`PROMPT_VERSION`, schema versions) and stored per insight | B | ✅ versioned |
| UI copy (EN/UZ/RU) | `frontend/src/i18n/locales` | standard i18n | translators edit JSON | B | ✅ |
| Demo accounts, demo leaderboard peers | `seed_demo*` commands | demo only | never run seeds against a pilot DB | C | ✅ isolated |
| Organizations, resources, learning paths, opportunities, circles, events | DB (demo catalog seeded from `seed_demo_ecosystem`, fictional orgs `is_demo=True`) | partner content | Django admin (activate, feature, order, deadlines, translations) | A | ✅ done |
| Community moderation | DB + Django admin (approve / reject / delete, reports) | safety operations | admin queue; 3 open reports auto-return a post to review | A | ✅ done |
| Matching thresholds & reason rules | `ecosystem/services/matching.py` | product logic; must stay explainable | versioned code, tested | B | ✅ |
| Resource / opportunity / circle images | frontend assets by `cover_key` | bundled images | upload via admin later | B→A | ⏳ later |
| Demo login prefill | frontend, `VITE_DEMO_MODE` | demo convenience | off in pilot builds (`VITE_DEMO_MODE=false`) | C | ✅ done |
| API URL, hosts, CORS, secrets, time zone, rates, TTLs | environment | per deployment | `.env.example`, `.env.docker.example` | D | ✅ |
| AI provider / model / timeouts | environment | per deployment | env; `groq_check`/`ai_check` commands | D | ✅ |

## 4. What was hardened for the POC (this milestone)

| Area | Before | After |
|---|---|---|
| Settings | dev defaults everywhere (fallback secret, DEBUG on) | `DJANGO_ENV=production` fails closed (weak/default secret, DEBUG, empty/`*` hosts refuse to start); HTTPS redirect, secure cookies, HSTS, nosniff, referrer policy, `X-Frame-Options: DENY`, proxy SSL header |
| Deployment | manual runserver | Dockerfiles (gunicorn, non-root, migrate/collectstatic on start), nginx SPA + proxy, docker-compose with PostgreSQL, env examples, whitenoise for admin static |
| CI | none | GitHub Actions: check, deploy check, migration check, backend tests on PostgreSQL, seed/reset idempotency; frontend `npm ci`, tests, typecheck, lint, build |
| Throttling | none | global anon/user limits + scoped limits: auth, parent connect, AI generation, Companion, redemption, account deletion (env-tunable) |
| Parent connection | permanent 5-digit code (90k space), no limits | learner-generated `GFT-XXXX-XXXX` (~8.5×10¹¹), single-use, 72 h expiry, revocable, regenerable, throttled; learner can remove a parent; legacy codes expired by migration |
| Auth | min length 6; refresh tokens never revoked; no logout | min 10 + similarity/common/numeric validators; refresh rotation + blacklist; logout revokes; password change invalidates tokens; account deletion; ADMIN never self-assignable; SPA clears cached data on logout |
| Content management | minimal admin; raw answers visible | admin for assessments/sections/questions/options/mappings, missions/steps/rules, rewards + fulfilment; learner records read-only; private content excluded |
| Assessment versioning | none; completed sessions re-scored against current mappings; `scoring_version` wrong ("v1") | `Assessment.version`, per-session `assessment_version` + correct `scoring_version` + frozen `result_snapshot`; locked content; draft/publish workflow |
| AI traceability | provider/model/language/input version | + `prompt_version`, `schema_version`, `latency_ms`, `failure_reason` per insight; Companion replies record provider/model/prompt version |
| Observability | print-style logs | request ids (`X-Request-ID`), JSON logs option, access log without content, `/health/live/` + `/health/ready/` (DB only), optional Sentry (`SENTRY_DSN`, no PII) |
| API docs | none | OpenAPI schema `/api/v1/schema/` + Swagger `/api/v1/docs/` (off in production unless enabled); each endpoint states its role and rate-limit scope |
| Placeholder routes | My Journey / Opportunities / Profile / Admin placeholders reachable | removed; admin accounts are pointed to Django admin (Opportunities is now a real feature — ecosystem milestone) |
| Private storage | local only | `PRIVATE_STORAGE_BACKEND=filesystem|s3` (optional `django-storages`), still streamed through owner checks |

## 5. Security / privacy

See `PRIVACY.md`. Parents never receive diary, Companion, mood, reflections, Today's Spark or
nudges (tested at API and AI-prompt level); Django admin excludes private content (tested).

## 6. Assessment engine

See `ASSESSMENT_METHOD.md`: deterministic, multi-signal, research-informed **early exploratory**
assessment; **not** a validated psychometric instrument; pilot validation plan included.

## 7. AI architecture

One provider interface (`generate_structured`), structured JSON output, Pydantic validation,
banned-phrase and source-grounding checks, deterministic fallback, persisted results, safe logs and
trace fields. AI interprets; it never scores. Keys never leave the backend.

## 8. Deployment

See `DEPLOYMENT.md`. Verified locally: production settings with gunicorn, whitenoise static,
health probes, security headers, JSON logs. Docker images/compose are written and syntax-checked,
**not yet built** (Docker was not available on the dev machine).

## 9. Testing / CI

Backend: 176 tests (unit + API + privacy boundaries + hardening + ecosystem), `check`, `check --deploy`,
`makemigrations --check`. Frontend: 60 Vitest tests, typecheck, lint, build. The same commands run in
`.github/workflows/ci.yml` (CI itself has not run yet — it starts on the next push).

## 10. Known limitations

- Assessment is short and unvalidated (see method doc); translations not psychometrically checked.
- No email verification, password reset or consent/age-gate flows (need an email provider and a legal basis).
- Throttle counters are per process (fine for one worker; shared cache needed when scaling).
- Tokens in localStorage (XSS-sensitive); no CSP header yet.
- Parent connection has a backend API only (student UI for generating codes not built yet).
- Leaderboard is global (no class/school scoping); demo peers exist only in demo seeds.
- Redemptions are reserved and fulfilled manually by staff in Django admin.
- Missions: only one; mission content is not version-locked (evidence is frozen at completion, so
  past results are safe, but in-progress attempts could see edited steps).
- Ecosystem: demo catalog only (fictional organizations, example.org links); no partner self-service,
  no notifications for new opportunities, no age/location on the learner (eligibility is "check"),
  community is text-only with manual moderation (no auto-filtering of personal details yet).
- AI provider free tier limits (Groq ~8k tokens/min); gpt-oss-20b occasionally returns malformed JSON (retried once, then fallback).

## 11. Required before production

1. Legal/consent: jurisdiction review (minors), consent capture, privacy notice, DPA with AI providers, data residency decision.
2. Identity: email verification, password reset, optional school/SSO onboarding; admin 2FA.
3. Security review / penetration test; CSP; move tokens to httpOnly cookies; dependency scanning.
4. Operations: managed PostgreSQL with PITR, media backups + restore drills, monitoring/alerting (Sentry, uptime), log retention.
5. Shared cache (Redis or DB cache) for throttling across workers; load test.
6. Assessment validation study (see method doc) and expert content review before any high-stakes use.
7. Data export + self-service deletion UI; retention jobs (inactive accounts, old AI insights).
8. Content operations: role-based staff permissions (content editor vs support), admin audit log.
9. Student UI for parent codes/connected parents; parent-side disconnect.
10. Accessibility audit (WCAG) and mobile navigation.
