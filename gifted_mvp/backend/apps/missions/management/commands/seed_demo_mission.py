"""Seed the flagship mission "Design a Better School Bag" (idempotent).

Steps are upserted by key (IDs stay stable, so in-progress responses survive a
re-seed). Evidence rules are replaced wholesale — they are pure configuration.
Weights are deliberately small: one mission adds evidence, it does not conclude.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.evidence.models import EvidenceKind as K
from apps.missions.models import Difficulty, Mission, MissionSignalMap, MissionStep, StepType
from apps.signals.models import Signal, SignalCategory

# Non-interest dimensions a mission can add evidence to (assessment never scores these).
MISSION_SIGNALS = [
    ("design_exposure", "Design & making exposure", SignalCategory.EXPOSURE),
    ("problem_solving", "Creative problem solving", SignalCategory.WORK_STYLE),
    ("prioritization", "Prioritization & trade-offs", SignalCategory.WORK_STYLE),
    ("user_thinking", "User thinking & empathy", SignalCategory.WORK_STYLE),
]

MISSION = {
    "slug": "design-a-better-school-bag",
    "title": "Design a Better School Bag",
    "short_description": (
        "Students say their bags are heavy, uncomfortable and hard to organize. "
        "Investigate the problem, work within a budget and choose a design direction."
    ),
    "context": "A short design challenge about real users, limited resources and trade-offs.",
    "difficulty": Difficulty.BEGINNER,
    "estimated_minutes": 8,
    "order": 1,
    "metadata": {
        "time_label": "5–8 min",
        "activity_label": "Design challenge",
        "focus_areas": ["Creative problem solving", "Prioritization", "User thinking", "Design exposure"],
        "intro_steps": [
            {"title": "Meet the users", "text": "Read what students say about their bags."},
            {"title": "Pick what to investigate", "text": "Choose the problems you'd study first."},
            {"title": "Spend a limited budget", "text": "10 points — you can't fix everything."},
            {"title": "Choose a direction", "text": "Pick the design that balances it best."},
            {"title": "Reflect", "text": "Explain your thinking in a few sentences."},
        ],
        "match_signals": ["artistic", "realistic"],
        "match_keywords": ["design", "build", "prototype", "creative", "making", "engineer", "invent", "construct"],
    },
}

STEPS = [
    {
        "key": "brief",
        "type": StepType.CONTEXT,
        "title": "The brief",
        "prompt": (
            "Students at your school say their bags are heavy, uncomfortable and hard to organize. "
            "The student council has asked a small design team — you — to propose a better school bag."
        ),
        "content": {
            "voices": [
                {"quote": "By the last lesson my shoulders really hurt.", "who": "Grade 8 student"},
                {"quote": "I can never find my calculator — everything ends up at the bottom.", "who": "Grade 9 student"},
                {"quote": "My tablet screen cracked inside my bag last term.", "who": "Grade 7 student"},
            ],
            "goal": "Your job: decide what to fix first — within real limits.",
        },
    },
    {
        "key": "understand",
        "type": StepType.MULTI_SELECT,
        "title": "Understand the user",
        "prompt": "Which problems would you investigate first? Pick up to two — a real team can't study everything at once.",
        "content": {
            "min": 1,
            "max": 2,
            "options": [
                {"key": "too_heavy", "label": "Too heavy", "description": "Bags weigh a lot by the end of the day.", "icon": "⚖️"},
                {"key": "hard_to_organize", "label": "Hard to organize", "description": "Things sink to the bottom and get lost.", "icon": "🗂️"},
                {"key": "uncomfortable_straps", "label": "Uncomfortable straps", "description": "Straps dig in and slip off shoulders.", "icon": "🎒"},
                {"key": "books_damaged", "label": "Books get damaged", "description": "Bent corners, torn pages, spilled drinks.", "icon": "📚"},
                {"key": "device_safety", "label": "No safe place for devices", "description": "Tablets and phones get knocked around.", "icon": "📱"},
            ],
        },
    },
    {
        "key": "prioritize",
        "type": StepType.BUDGET,
        "title": "Prioritize",
        "prompt": "You have 10 points to spend on improvements. You can't afford everything — choose what matters most.",
        "content": {
            "budget": 10,
            "min_items": 1,
            "options": [
                {"key": "lightweight_material", "label": "Stronger, lighter material", "description": "Cuts weight without losing strength.", "cost": 4, "icon": "🪶"},
                {"key": "ergonomic_straps", "label": "Ergonomic straps", "description": "Padded, adjustable, spreads the load.", "cost": 3, "icon": "🧍"},
                {"key": "modular_compartments", "label": "Modular compartments", "description": "A place for everything, rearrangeable.", "cost": 3, "icon": "🧩"},
                {"key": "waterproof_layer", "label": "Waterproof layer", "description": "Keeps books dry in rain and spills.", "cost": 2, "icon": "💧"},
                {"key": "device_protection", "label": "Padded device sleeve", "description": "Protects tablets and laptops from knocks.", "cost": 3, "icon": "🛡️"},
            ],
        },
    },
    {
        "key": "direction",
        "type": StepType.SINGLE_CHOICE,
        "title": "Choose a design direction",
        "prompt": "Which direction best balances what users need with what you can afford?",
        "content": {
            "options": [
                {"key": "featherweight", "label": "The Featherweight", "description": "As light as possible — easy to carry all day.", "tradeoff": "Fewer compartments", "icon": "🪶"},
                {"key": "organizer", "label": "The Organizer", "description": "Modular inside, so everything has its place.", "tradeoff": "A little heavier", "icon": "🧩"},
                {"key": "comfort_fit", "label": "The Comfort Fit", "description": "Built around the body: padded back, adjustable straps.", "tradeoff": "Bulkier look", "icon": "🧍"},
                {"key": "statement", "label": "The Statement Bag", "description": "A look students are proud of, with swappable panels.", "tradeoff": "Style uses budget", "icon": "🎨"},
            ],
        },
    },
    {
        "key": "reflect",
        "type": StepType.REFLECTION,
        "title": "Reflect",
        "prompt": "There's no right answer here — we're interested in how you thought about it.",
        "content": {
            "fields": [
                {"key": "why", "label": "Why did you choose these improvements?", "placeholder": "I focused on… because…", "required": True, "min_length": 20, "max_length": 600},
                {"key": "test_first", "label": "If you could build a prototype, what would you test first?", "placeholder": "I would test… by…", "required": False, "max_length": 400},
            ],
        },
    },
]

# (step_key or None, option_key, signal_key, kind, weight, observation)
RULES = [
    (None, "", "design_exposure", K.EXPOSURE, "0.50", "Completed a hands-on design challenge"),
    (None, "", "artistic", K.ENGAGEMENT, "0.20", "Worked through a design problem end to end"),
    ("understand", "", "user_thinking", K.ENGAGEMENT, "0.30", "Started from users' real complaints"),
    ("understand", "too_heavy", "user_thinking", K.ENGAGEMENT, "0.10", "Investigated physical comfort"),
    ("understand", "uncomfortable_straps", "user_thinking", K.ENGAGEMENT, "0.10", "Investigated physical comfort"),
    ("understand", "hard_to_organize", "problem_solving", K.REASONING, "0.20", "Chose to investigate an organization problem"),
    ("understand", "books_damaged", "realistic", K.ENGAGEMENT, "0.20", "Considered practical protection"),
    ("understand", "device_safety", "realistic", K.ENGAGEMENT, "0.20", "Considered practical protection"),
    ("prioritize", "", "prioritization", K.DECISION, "0.50", "Made trade-offs within a fixed budget"),
    ("prioritize", "ergonomic_straps", "user_thinking", K.DECISION, "0.20", "Spent budget on user comfort"),
    ("prioritize", "modular_compartments", "problem_solving", K.DECISION, "0.20", "Spent budget on a structural fix"),
    ("prioritize", "lightweight_material", "realistic", K.ENGAGEMENT, "0.20", "Chose practical material improvements"),
    ("prioritize", "waterproof_layer", "realistic", K.ENGAGEMENT, "0.10", "Chose practical material improvements"),
    ("prioritize", "device_protection", "realistic", K.ENGAGEMENT, "0.10", "Chose practical protection"),
    ("direction", "", "prioritization", K.DECISION, "0.30", "Committed to one direction and its trade-off"),
    ("direction", "statement", "artistic", K.INTEREST, "0.40", "Chose a direction led by look and identity"),
    ("direction", "comfort_fit", "user_thinking", K.DECISION, "0.30", "Chose a direction built around the user's body"),
    ("direction", "organizer", "problem_solving", K.DECISION, "0.30", "Chose a direction built around a system"),
    ("direction", "featherweight", "realistic", K.INTEREST, "0.30", "Chose a practical, engineering-led direction"),
    ("reflect", "why", "prioritization", K.REFLECTION, "0.20", "Explained the reasoning behind the choices"),
    ("reflect", "test_first", "problem_solving", K.REASONING, "0.30", "Proposed what a prototype should test first"),
]


class Command(BaseCommand):
    help = "Seed the flagship mission 'Design a Better School Bag' (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        for key, label, category in MISSION_SIGNALS:
            Signal.objects.update_or_create(key=key, defaults={"label": label, "category": category, "is_active": True})

        mission, _ = Mission.objects.update_or_create(
            slug=MISSION["slug"], defaults={k: v for k, v in MISSION.items() if k != "slug"}
        )
        steps = {}
        for order, spec in enumerate(STEPS, start=1):
            step, _ = MissionStep.objects.update_or_create(
                mission=mission, key=spec["key"], defaults={**{k: v for k, v in spec.items() if k != "key"}, "order": order}
            )
            steps[spec["key"]] = step
        MissionStep.objects.filter(mission=mission).exclude(key__in=steps).delete()

        signals = {s.key: s for s in Signal.objects.filter(key__in={r[2] for r in RULES})}
        missing = {r[2] for r in RULES} - set(signals)
        if missing:
            raise RuntimeError(f"Seed the assessment first; missing signals: {sorted(missing)}")
        MissionSignalMap.objects.filter(mission=mission).delete()
        MissionSignalMap.objects.bulk_create(
            MissionSignalMap(
                mission=mission,
                step=steps[step_key] if step_key else None,
                option_key=option_key,
                signal=signals[signal_key],
                kind=kind,
                weight=Decimal(weight),
                observation=obs,
            )
            for step_key, option_key, signal_key, kind, weight, obs in RULES
        )
        self.stdout.write(f"Seeded mission '{mission.title}' with {len(steps)} steps and {len(RULES)} evidence rules.")
