# Gifted — Demo Quick Guide

All commands run from `gifted_mvp/`. Backend uses port **8001** (8000 belongs to another local project).

## Start backend
```
cd backend
.venv/bin/python manage.py runserver 127.0.0.1:8001
```
First time on a machine: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` and create `backend/.env` from `.env.example`.

## Start frontend
```
cd frontend
npm install        # first time only
npm run dev        # http://localhost:5173
```

## Migrate
```
cd backend && .venv/bin/python manage.py migrate
```

## Seed demo (idempotent)
```
cd backend && .venv/bin/python manage.py seed_demo
```
Demo accounts, Discovery Assessment, mission, parent link, reward catalog, 6 safe demo leaderboard peers.

## Reset demo — run right before presenting (idempotent)
```
cd backend && .venv/bin/python manage.py reset_demo
```
Demo student → NOT_STARTED: clears assessment sessions, AI insights, Passport, evidence, mission attempt,
Companion chats, diary entries + photos, activity/points/streak, badges, redemptions, Today's Spark and
bell state. Keeps seeded content, the parent link, rewards and demo peers (their weekly activity is refreshed).

## Groq check
`backend/.env`: `AI_PROVIDER=groq`, `GROQ_API_KEY=<key>` (model default `openai/gpt-oss-20b`).
```
cd backend && .venv/bin/python manage.py groq_check     # expect outcome=ai
```
Free tier ≈ 8k tokens/min — leave ~30 s between full rehearsals, then `reset_demo` again.

## Before a demo after pulling this version
`migrate` (new tables/fields) → `seed_demo` → `reset_demo`. Old browser sessions must sign in again
(tokens now carry a revocation claim). Demo logins are prefilled only when `VITE_DEMO_MODE` isn't `false`.

## Student login
`student@gifted.demo` / `demo123` (prefilled on the Student tab).

## Parent login
`parent@gifted.demo` / `demo123` (click the **Parent** tab — it prefills).

## Demo flow (~10 min)
1. **Landing** → Sign in (student).
2. **Home** — welcome state, Today's Spark, empty diary + momentum.
3. **Assessment** — 10 short items (switch UZ/RU mid-way to show language; progress stays) → Complete.
4. **AI Emerging Profile** ("AI-assisted insight") → Build My Gifted Passport.
5. **Gifted Passport** (Emerging) → the next-exploration card (**Explore this next** / **Try this mission**).
6. **Mission** "Design a Better School Bag" → 5 steps → Complete → **View Updated Passport** (Growing, journey 2/5).
7. **AI Companion** — share a proud moment, e.g. *"Today I presented my project and felt proud"* → live answer → **Add to My Diary**.
8. **My Diary** — the draft holds only your words → pick a mood / sticker → **Save entry** → back to My Diary.
9. **Streak & Rewards** — points (40 + 60 + 10 + 15), streak, badges, leaderboard; redeem the Sticker Pack.
10. **Home** — Today's Spark + the updates bell (badges, Passport, reward).
11. Sign out → **Parent** tab → **Parent Dashboard** → **Parent Insights** (progress + guidance only; no diary, chat or mood).

## Emergency AI fallback
Nothing to do: every AI screen falls back automatically to **Signal-based insight / guidance**, and the
Companion shows a calm "try again" message (it never fakes an answer). If the API is slow in the room:
set `AI_PROVIDER=stub` in `backend/.env`, restart the backend, `reset_demo` — everything runs instantly on
the signal-based fallback (the Companion will then say it can't answer right now).
