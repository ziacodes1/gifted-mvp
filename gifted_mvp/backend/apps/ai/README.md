# apps/ai — AI domain (architecture only for now)

AI operates **on top of** structured learner data. Scoring/assessment signals are
deterministic and computed elsewhere; the LLM never invents scores.

Flow: `React → Django API → ai.services → LLM provider`. The API key lives only on
the backend. Providers are swappable via `AI_PROVIDER` in settings.

Layout:
- `schemas/` — structured input/output contracts (validated, provider-agnostic).
- `prompts/` — prompt text, kept out of business logic.
- `services/` — orchestration: build input from domain data, call a provider,
  validate the output against a schema, fall back gracefully.

Planned services (not implemented yet):
- **Profile Synthesis** — signals/confidence/exposure/evidence → summary,
  emerging_strengths, exposure_gaps, uncertainty_notes, suggested_explorations.
- **Next-Step Recommendation** — profile/interests/reasoning/gaps/evidence →
  recommended_activity, explanation, signals_used, intended_validation.
- Later: mission generation, parent insights.
