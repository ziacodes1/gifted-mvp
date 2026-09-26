"""Today's Spark catalog + selection weights. All copy lives in the frontend locales under
`sparks.items.<key>` (and `sparks.facts[i]`); the backend only chooses keys.

Nothing here is AI-generated and nothing is chosen from private content: selection uses
assessment/mission status, Passport stage, streak and diary *counts/dates* only.
"""
from dataclasses import dataclass, field


class SparkType:
    REFLECTION = "REFLECTION"
    MINI_CHALLENGE = "MINI_CHALLENGE"
    FACT = "FACT"
    NEXT_STEP = "NEXT_STEP"
    DIARY_PROMPT = "DIARY_PROMPT"
    COMPANION_PROMPT = "COMPANION_PROMPT"
    MISSION_NUDGE = "MISSION_NUDGE"


@dataclass(frozen=True)
class Spark:
    key: str
    type: str
    route: str | None = None  # companion | diary | mission | passport | assessment
    actions: tuple[str, ...] = field(default_factory=tuple)  # diary | companion | go | complete


SPARKS = [
    # Reflections — lighter content, always available.
    Spark("reflect_no_fail", SparkType.REFLECTION, None, ("diary", "companion")),
    Spark("reflect_learned_self", SparkType.REFLECTION, None, ("diary", "companion")),
    Spark("reflect_lost_time", SparkType.REFLECTION, None, ("diary", "companion")),
    Spark("reflect_proud", SparkType.REFLECTION, None, ("diary",)),
    Spark("reflect_curious", SparkType.REFLECTION, None, ("companion", "diary")),
    # Mini challenges — small, offline, completable once a day.
    Spark("ch_ask_field", SparkType.MINI_CHALLENGE, None, ("complete",)),
    Spark("ch_three_solutions", SparkType.MINI_CHALLENGE, None, ("complete",)),
    Spark("ch_new_field_fact", SparkType.MINI_CHALLENGE, None, ("complete",)),
    Spark("ch_explain_simple", SparkType.MINI_CHALLENGE, None, ("complete",)),
    Spark("ch_understand_better", SparkType.MINI_CHALLENGE, None, ("complete",)),
    Spark("ch_outside_interests", SparkType.MINI_CHALLENGE, None, ("complete",)),
    # State-driven next actions.
    Spark("ns_start_discovery", SparkType.NEXT_STEP, "assessment", ("go",)),
    Spark("ns_continue_assessment", SparkType.NEXT_STEP, "assessment", ("go",)),
    Spark("ns_passport_updated", SparkType.NEXT_STEP, "passport", ("go",)),
    Spark("mn_try_mission", SparkType.MISSION_NUDGE, "mission", ("go",)),
    Spark("dp_first_page", SparkType.DIARY_PROMPT, "diary", ("diary",)),
    Spark("dp_come_back", SparkType.DIARY_PROMPT, "diary", ("diary",)),
    Spark("cp_interests", SparkType.COMPANION_PROMPT, "companion", ("companion",)),
    Spark("cp_plan_week", SparkType.COMPANION_PROMPT, "companion", ("companion",)),
]
SPARKS_BY_KEY = {s.key: s for s in SPARKS}

FACT_COUNT = 20  # sparks.facts has exactly this many entries in every locale
FACT = Spark("fact", SparkType.FACT, None, ("companion",))

MINI_CHALLENGE_POINTS = 5  # see engagement.rules — once per day

DIARY_NUDGE_AFTER_DAYS = 3
RECENT_DAYS = 3  # "recent" mission completion for the Passport nudge
DIARY_MILESTONES = (5, 10, 25, 50, 100)
NUDGE_WINDOW_DAYS = 7


def spark_for(key: str) -> Spark:
    if key.startswith("fact_"):
        return FACT
    return SPARKS_BY_KEY[key]
