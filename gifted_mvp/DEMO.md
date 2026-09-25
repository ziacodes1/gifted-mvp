# Gifted — Demo Quick Guide

## Start backend
```
cd gifted_mvp/backend
.venv/bin/python manage.py runserver 127.0.0.1:8001
```
(Port 8001: 8000 is used by another local project.)

## Start frontend
```
cd gifted_mvp/frontend
npm run dev          # http://localhost:5173
```

## Reset demo (run right before presenting)
```
cd gifted_mvp/backend
.venv/bin/python manage.py reset_demo
```
Student goes back to NOT_STARTED; parent stays connected; content is kept. Safe to run any number of times.

## Student login
`student@gifted.demo` / `demo123` — the login page prefills it (Student tab).

## Parent login
`parent@gifted.demo` / `demo123` — click the **Parent** tab on the login page (prefills it).

## Demo flow
1. Student → Sign in → Dashboard → **Start Assessment** → 10 mixed items (activities, situations, 2 puzzles) → **Complete**
2. Emerging Profile (AI-assisted insight + assessment signals) → **Build My Gifted Passport**
3. Passport → **Explore this next** → Mission → **Start challenge** → 5 steps → **Complete mission**
4. **View Updated Passport** → now *Growing Passport*, 1 exploration mission, journey at Explore
5. Sign out → Parent tab → Sign in → Parent Dashboard → **Parent Insights**

## AI check (before the demo)
In `backend/.env` (never commit keys) — pick one provider:
```
AI_PROVIDER=groq               # recommended (fastest); or: gemini / anthropic / stub
GROQ_API_KEY=<your key>        # for groq (model default: openai/gpt-oss-20b)
GEMINI_API_KEY=<your key>      # for gemini
AI_API_KEY=<your key>          # for anthropic
AI_MODEL=                      # empty = auto (gemini: newest stable Flash; anthropic: claude-opus-5)
```
Then `cd backend && .venv/bin/python manage.py groq_check` (Groq) or `ai_check` (any provider) — it prints the model and `outcome=ai` (or
`outcome=fallback reason=...`, e.g. `auth_failed`, `quota_exceeded`, `billing_credit_low`). Pin the printed
model in `AI_MODEL`, restart the backend, `reset_demo`, do one quick run: the backend log should show
`ai feature=profile_synthesis provider=groq ... outcome=ai` and the UI badge **AI-assisted insight**.
Groq free tier ≈ 8k tokens/min: wait ~30 s between full rehearsals or you may see `reason=rate_limited` (fallback).
Run `reset_demo` again afterwards — insights are saved per learner, so the rehearsal's would be reused.

## Emergency fallback (AI unavailable during the live demo)
Nothing to do — every AI screen falls back automatically to **Signal-based insight / guidance**
and the flow continues. If a slow API is holding up the room, set `AI_PROVIDER=stub` in `.env`,
restart the backend, and `reset_demo`: everything then runs instantly on the signal-based fallback.
