# Gifted Discovery Assessment — Method

> **What it is:** a deterministic, multi-signal, research-informed, **early exploratory** assessment.
> **What it is not:** a validated psychometric instrument. No reliability or validity study has been
> run yet. Results are starting points for exploration, never verdicts about a learner.

Code: `backend/apps/assessments/services/scoring.py` (scoring), `apps/signals` (signal catalogue and
option→signal rules), `apps/questions` (items), `apps/assessments/versioning.py` (content versions).

## 1. Structure

The current version (`gifted-discovery`, version 1) has **10 items** in 6 formats: visual choice (3),
pattern puzzle (2), value trade-off (2), story choice (1), scenario choice (1), multi-select (1).
Items and options are database content, editable in Django admin until the version is used (§7).

## 2. Signal categories — kept separate on purpose

| Category | Count | What it means | What it does **not** mean |
|---|---|---|---|
| INTEREST | 5 (RIASEC-inspired: realistic, investigative, artistic, social, enterprising) | what the learner is drawn to | ability or talent |
| APTITUDE | 2 (logical, spatial reasoning) | 1–2 short puzzles answered | a measured ability |
| WORK_STYLE | 4 | self-described ways of working | a personality type |
| VALUE | 4 | what matters to the learner in a trade-off | fixed character |
| EXPOSURE | 5 | what the learner says they have tried | skill |

**Interest ≠ Ability ≠ Exposure.** The categories are never combined into one score, never ranked
against each other, and presented separately in every screen and every AI prompt.

## 3. Deterministic scoring (no AI)

Each option can map to one or more signals with a weight (`ResponseSignalMap`). For each signal:

- **opportunity_count** = answered items that *offered* at least one option mapped to the signal
- **evidence_count** = selected options that map to it
- **score** = weighted picks ÷ opportunities × 100 (0–100, capped)

Scoring against *opportunities* (not all answers) keeps categories comparable: a reasoning signal
offered by one puzzle is not diluted by nine interest items. Zero-evidence rows are stored too, so
"not tried yet" is visible. A wrong puzzle answer produces **no evidence — never negative evidence**.

## 4. Confidence (conservative by design)

| Category | Rule |
|---|---|
| APTITUDE, EXPOSURE | always **LOW** (one or two puzzles / a self-report) |
| INTEREST | **MEDIUM** only if picked ≥ 3 times *and* score ≥ 50; otherwise LOW |
| WORK_STYLE, VALUE | MEDIUM if picked ≥ 2 times; otherwise LOW |

A 10-item assessment never yields HIGH confidence. The UI shows "Picked X of Y times" instead of
implying precision.

## 5. AI is not used for scoring

Scores exist before any AI call and are stored in `LearnerSignal` and, frozen, in the session's
`result_snapshot`. The AI receives these already-computed values and writes an *interpretation*
(headline, strengths, gaps, next step). Its output is schema-validated, checked for banned
deterministic phrases ("you should become…", "you are definitely…"), and replaced by a deterministic
fallback if anything fails. The AI can never change a score.

## 6. Mission evidence is separate

Missions record their own `Evidence` through fixed, admin-managed rules (`MissionSignalMap`:
completion / step answered / option chosen → signal, kind, weight). Mission evidence **never
modifies assessment scores**; it is shown beside them ("explored through missions") with its source.

## 7. Versioning — what happens when content changes

- `Assessment.version` identifies the content version; `AssessmentSession.assessment_version`
  records which version a learner took, `scoring_version` (currently `s2`) the rules applied, and
  `result_snapshot` the exact signals computed at completion.
- A version becomes **locked** as soon as one learner has a session: its items, options and signal
  mappings are read-only in admin. Changes go into a **new draft version** (admin action: copy
  content → edit → publish). Publishing activates the new version and deactivates the old one.
- Old sessions keep their version and snapshot, so their results are **never re-interpreted** with
  new content or rules (tested).

Changes that require a new **content** version: adding/removing/reordering items or options, changing
option→signal mappings or weights, changing an item's meaning. Changes that require a new
**scoring** version (`SCORING_VERSION` in code): the formula, confidence thresholds, evidence rules.
Pure translation typo fixes currently also require a new version (strict POC rule).

## 8. Limitations of the current assessment

- 10 items: each signal has few opportunities (often 1–5), so scores are coarse and unstable.
- Forced choice and ipsative formats: picking one interest lowers others; scores are *within-learner*
  preferences, not comparable population measures.
- Aptitude = 1–2 puzzles: indicative at most.
- Exposure is self-reported and depends on access and opportunity, not ability.
- Item content and images were designed by the team, not yet reviewed by independent experts.
- Translations (EN/UZ/RU) have not been checked for measurement equivalence.
- No norms: there is no reference population.

## 9. Pilot validation plan

Collected only with appropriate consent (see `PRIVACY.md`), aggregated and de-identified:

1. **Item distribution** — option pick rates per item; items nobody picks or everybody picks.
2. **Completion and drop-off** — where learners stop; time-to-complete.
3. **Response timing** — very fast answers (inattention) and slow items (confusing wording).
4. **Signal distribution** — spread of scores per signal; floor/ceiling effects.
5. **Test–retest stability** — a retake after 2–4 weeks for a volunteer subgroup; agreement of top interests.
6. **Language comparison** — EN/UZ/RU distributions for the same items (translation effects).
7. **Mission follow-through** — do learners with an interest signal choose/complete related missions?
8. **Learner feedback** — "does this feel like me?" and "what would you change?" after results.
9. **Expert review** — item content review by educators/psychologists before any wider use.

Until these are done, Gifted presents results as *early signals to explore*, which is how the product
and every AI prompt already frame them.
