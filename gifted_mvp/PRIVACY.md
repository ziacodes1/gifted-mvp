# Gifted — Technical Privacy & Data Lifecycle

> This describes how the software separates and protects data. It is **not** a legal assessment.
> Consent, age thresholds, data-residency and retention obligations depend on the pilot
> jurisdiction and partner institution and must be settled before a pilot with real learners.

Gifted's users are mostly minors. The design rule: **parents and staff see growth, not private thoughts.**

## 1. Data classes

| Class | Examples | Who can read it |
|---|---|---|
| **Student-private** | diary entries (title, body, mood, tags, stickers, photos), AI Companion conversations, mission reflection text, raw assessment answers, Today's Spark state, in-app nudges | the learner only (owner-scoped API; other learners get 404) |
| **Parent-safe** | Passport status and journey, deterministic signals (score/confidence/counts), evidence counts and explored dimensions, activity titles/dates, AI parent guidance | the learner and connected parents |
| **Aggregate / public** | leaderboard rows: rank, first name + last initial, weekly points | signed-in students |
| **Operational** | account email/role, activity event types (no content), AI trace metadata | the learner; staff via Django admin |

## 2. Enforcement points (all covered by tests)

- **Parent API** (`apps/parents`): every learner lookup goes through `get_connected_learner`
  (unconnected → 404); the overview is a projection of the Passport read model and never touches
  diary, Companion, mission responses or raw answers. The parent AI insight input is built from the
  same projection. Tests assert private strings never appear in parent responses or in the prompt
  sent to the parent-insight model.
- **Role permissions:** diary, Companion, engagement and Today endpoints are `IsStudent` → parents 403.
- **AI prompts:** the Companion's context is the Passport projection (no names/emails/answers/
  reflections/diary). The diary is never sent to any AI provider.
- **Engagement:** the diary hook passes only `entry:<id>` and a date; `ActivityEvent` has no content fields.
- **Django admin:** diary, Companion, raw assessment answers, mission responses and Today state are
  **not registered**; learner records that are visible (sessions, signals, evidence, Passport,
  activity, AI insights) are read-only (tested).
- **Photos:** validated with Pillow, re-encoded to WebP (drops EXIF/GPS), stored under random names
  outside any public URL (filesystem) or in a private bucket (S3 mode), streamed only by an
  owner-checked view with `Cache-Control: private`.
- **Logs:** request logs contain method, path, status, duration and a request id; AI logs contain
  feature/provider/model/outcome/latency/failure category. No prompts, tokens or learner text.
- **Parent connection:** only the learner can create a code; codes are random (GFT-XXXX-XXXX),
  single-use, expire (72 h default), can be revoked, and redemption is rate-limited. The learner can
  remove a connected parent at any time.

## 3. Account & data deletion

`DELETE /api/v1/auth/me/` with the account password permanently deletes the user and — through
`on_delete=CASCADE` — all of their learner data: assessment sessions and answers, signals, evidence,
Passport, mission attempts, AI insights, Companion conversations, diary entries **and photo files**,
engagement events, badges, redemptions, Today state, parent links and connection codes. Outstanding
refresh tokens are removed. (Tested: files are deleted, other users are untouched.)

Not yet available (pre-pilot work): a UI button for deletion, parent-initiated deletion requests,
data export (a portable copy of a learner's data), and deletion of backups older than the retention
window (see §5).

## 4. Retention considerations (to decide per pilot)

- Diary and Companion data exist only for the learner's benefit: retain while the account exists;
  delete with the account. Consider an inactivity limit (e.g. delete after 12 months without login).
- AI insights are regenerable: they can be purged at any time without losing the learner's record.
- Aggregated, de-identified statistics for assessment validation (see `ASSESSMENT_METHOD.md` §9)
  should be derived without diary/Companion content and only with consent.
- Logs: keep short (e.g. 30 days); they contain no content but do contain request paths and ids.

## 5. Backups (operational requirement, not provided by the app)

- **PostgreSQL:** daily automated backups with point-in-time recovery if the platform offers it;
  encrypted at rest; restore tested before the pilot and then monthly.
- **Private media:** the diary photo store (volume or bucket) must be backed up alongside the
  database — a DB restore without matching files leaves broken photo references; bucket versioning
  is the simplest option.
- **Restore drill:** restore DB + media into a staging copy, run `manage.py check` and log in as a
  test learner to confirm diary photos load.
- **Deletion vs backups:** deleted accounts persist in backups until they age out; document the
  backup retention period (e.g. 30 days) in the pilot's privacy notice.

## 6. Known gaps (honest list)

- No email verification or password-reset email yet (needs an email provider).
- No consent records or age gate in the product yet.
- No field-level encryption: private data is protected by access control and database/storage
  encryption at rest provided by the hosting platform.
- Staff with database access can read everything; access must be limited to named operators.
- Tokens are stored in the browser's localStorage (standard for SPAs, but XSS-sensitive); a
  cookie-based session would be stronger for production.
