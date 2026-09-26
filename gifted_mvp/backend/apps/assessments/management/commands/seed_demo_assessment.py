"""Seed the demo Discovery assessment v2 (idempotent).

10 mixed-format items across all five signal categories. Learners only ever see
concrete activities/situations — category labels live in the hidden
`ResponseSignalMap` rows below. Puzzle answers are likewise only in the mappings.
Content is original. The v1 "Interests Discovery" set (if present) is deactivated,
never duplicated. English here is canonical; Uzbek/Russian come from `_assessment_i18n`
and are stored in each row's `translations` (presentation only — mappings are shared).
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.assessments.models import Assessment, AssessmentSection
from apps.questions.models import Question, QuestionOption, QuestionType as T
from apps.signals.models import ResponseSignalMap, Signal, SignalCategory as C

from . import _assessment_i18n as i18n

SLUG = "gifted-discovery"
LEGACY_SLUGS = ["interests-discovery"]

SIGNALS = {
    # key: (label, category)
    "realistic": ("Technology & Building", C.INTEREST),
    "investigative": ("Science & Investigation", C.INTEREST),
    "artistic": ("Art & Design", C.INTEREST),
    "social": ("Helping People", C.INTEREST),
    "enterprising": ("Leadership & Organizing", C.INTEREST),
    "logical_reasoning": ("Number patterns", C.APTITUDE),
    "spatial_reasoning": ("Spatial reasoning", C.APTITUDE),
    "structured_planning": ("Plans before acting", C.WORK_STYLE),
    "independent_work": ("Works independently", C.WORK_STYLE),
    "problem_solving": ("Creative problem solving", C.WORK_STYLE),
    "user_thinking": ("User thinking & empathy", C.WORK_STYLE),
    "value_originality": ("Creating something original", C.VALUE),
    "value_helpfulness": ("Being useful to others", C.VALUE),
    "value_discovery": ("Discovering new things", C.VALUE),
    "value_practical": ("Improving everyday things", C.VALUE),
    "exp_technology": ("Building & coding", C.EXPOSURE),
    "exp_science": ("Science experiments", C.EXPOSURE),
    "exp_design": ("Art & design", C.EXPOSURE),
    "exp_organizing": ("Organizing events", C.EXPOSURE),
    "exp_helping": ("Teaching & supporting others", C.EXPOSURE),
}


def _norm(cells):
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    return sorted([r - r0, c - c0] for r, c in cells)


def _rot90(cells):
    return _norm([(c, -r) for r, c in cells])


def _mirror(cells):
    return _norm([(r, -c) for r, c in cells])


# A chiral pentomino: rotations look alike, mirror images don't.
SHAPE = _norm([(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)])
OTHER_SHAPE = _norm([(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)])


def opt(value, label, maps=(), description="", image="", content=None):
    return {"value": value, "label": label, "description": description, "image": image,
            "content": content or {}, "maps": maps}


QUESTIONS = [
    {
        "type": T.VISUAL_CHOICE,
        "prompt": "Your school gives you one free afternoon to try something new. What would you pick first?",
        "helper_text": "Go with your first instinct.",
        "options": [
            opt("build-robot", "Build and test a small robot", [("realistic", 1)],
                image="interest_technology_robotics_girl_workshop"),
            opt("microscope", "Look at pond water under a microscope", [("investigative", 1)],
                image="interest_science_microscope_girl_lab_overalls"),
            opt("paint-canvas", "Paint a big canvas with no rules", [("artistic", 1)],
                image="interest_art_painting_girl_canvas_studio"),
            opt("help-learn", "Help a younger student with a tricky topic", [("social", 1)],
                image="interest_helping_tutoring_older_girl_younger_boy"),
        ],
    },
    {
        "type": T.STORY_CHOICE,
        "prompt": "Your class is building a stand for the school fair, and nobody knows where to start. What do you naturally do first?",
        "helper_text": "Pick what you'd actually do — not what sounds best.",
        "options": [
            opt("sketch", "Sketch a few ideas for how it could look", [("artistic", 1)]),
            opt("how-built", "Work out how it could actually be built", [("realistic", 1), ("problem_solving", Decimal("0.5"))]),
            opt("ask-visitors", "Ask a few visitors what they'd want to see", [("social", 1), ("user_thinking", 1)]),
            opt("split-jobs", "Split up the jobs and make a plan", [("enterprising", 1), ("structured_planning", 1)]),
        ],
    },
    {
        "type": T.PATTERN_CHOICE,
        "prompt": "Which number comes next?",
        "helper_text": "Look at how the gaps between numbers change.",
        "content": {"stimulus": {"kind": "sequence", "items": ["3", "5", "9", "15", "23", "?"]}},
        "options": [
            opt("n29", "29"),
            opt("n31", "31"),
            opt("n33", "33", [("logical_reasoning", 1)]),
            opt("n35", "35"),
        ],
    },
    {
        "type": T.VISUAL_CHOICE,
        "prompt": "Which of these projects would you happily spend a whole month on?",
        "helper_text": "Imagine you'd have time, tools and help.",
        "options": [
            opt("redesign-backpack", "Redesign a backpack so it's easier to carry", [("artistic", 1), ("realistic", Decimal("0.5"))],
                image="interest_product_design_backpack_prototype_girl_workshop"),
            opt("survey-patterns", "Find patterns in your school's survey results", [("investigative", 1)],
                image="interest_data_analysis_girl_laptop_charts"),
            opt("school-garden", "Grow and look after a school vegetable garden", [("realistic", Decimal("0.5")), ("investigative", Decimal("0.5"))],
                image="interest_nature_gardening_girl_planting_outdoors"),
            opt("pitch-council", "Pitch an idea to the school council and win support", [("enterprising", 1)],
                image="interest_leadership_group_presentation_whiteboard_green_sweater"),
        ],
    },
    {
        "type": T.SCENARIO_CHOICE,
        "prompt": "What would you most likely do?",
        "helper_text": "",
        "content": {"scenario": "Your group project is due in two days. One teammate hasn't done their part and isn't answering messages."},
        "options": [
            opt("check-in", "Message them privately to check they're okay", [("social", Decimal("0.5")), ("user_thinking", 1)]),
            opt("re-plan", "Re-plan the work so the group can still finish", [("structured_planning", 1), ("enterprising", Decimal("0.5"))]),
            opt("do-it-myself", "Quietly do their part yourself", [("independent_work", 1)]),
            opt("tell-teacher", "Let the teacher know early so there are no surprises", [("structured_planning", Decimal("0.5"))]),
        ],
    },
    {
        "type": T.VALUE_TRADEOFF,
        "prompt": "If you could only choose one outcome for your next project, which would feel more meaningful?",
        "helper_text": "Neither answer is better.",
        "options": [
            opt("original", "Create something completely original", [("value_originality", 1)],
                description="Something nobody has made before."),
            opt("useful", "Create something useful for many people", [("value_helpfulness", 1)],
                description="Something lots of people would actually use."),
        ],
    },
    {
        "type": T.MULTI_SELECT,
        "prompt": "Which of these have you actually tried before?",
        "helper_text": "Choose all that apply — this is about experience, not skill.",
        "content": {"min": 1, "max": 7},
        "options": [
            opt("built", "Built or repaired something with tools", [("exp_technology", 1)], content={"icon": "🔧"}),
            opt("coded", "Tried coding or programming", [("exp_technology", 1)], content={"icon": "💻"}),
            opt("science-kit", "Used a microscope or science kit", [("exp_science", 1)], content={"icon": "🔬"}),
            opt("digital-art", "Made digital art or a design", [("exp_design", 1)], content={"icon": "🎨"}),
            opt("organized", "Helped organize an event", [("exp_organizing", 1)], content={"icon": "📋"}),
            opt("taught", "Taught or supported someone", [("exp_helping", 1)], content={"icon": "🤝"}),
            opt("none", "None of these yet", content={"icon": "✨", "exclusive": True}),
        ],
    },
    {
        "type": T.PATTERN_CHOICE,
        "prompt": "Which shape is the same as this one — only turned?",
        "helper_text": "Shapes can be turned, but not flipped over.",
        "content": {"stimulus": {"kind": "shape", "cells": SHAPE}},
        "options": [
            opt("shape-a", "A", content={"cells": _mirror(_rot90(SHAPE))}),
            opt("shape-b", "B", [("spatial_reasoning", 1)], content={"cells": _rot90(SHAPE)}),
            opt("shape-c", "C", content={"cells": OTHER_SHAPE}),
            opt("shape-d", "D", content={"cells": _mirror(SHAPE)}),
        ],
    },
    {
        "type": T.VISUAL_CHOICE,
        "prompt": "There's a free weekend workshop in town. Which one do you sign up for?",
        "helper_text": "",
        "options": [
            opt("repair-electronics", "Fix old electronics at a maker fair", [("realistic", 1)],
                image="interest_technology_robotics_boy_workshop"),
            opt("museum-lab", "A hands-on lab day at the science museum", [("investigative", 1)],
                image="interest_science_microscope_girl_lab_dark_cardigan"),
            opt("run-desk", "Run the welcome team at a youth festival", [("enterprising", 1)],
                image="interest_leadership_group_presentation_whiteboard_black_shirt"),
            opt("homework-buddy", "Volunteer as a homework buddy at the library", [("social", 1)],
                image="interest_helping_tutoring_older_girl_younger_girl"),
        ],
    },
    {
        "type": T.VALUE_TRADEOFF,
        "prompt": "Which kind of challenge sounds more exciting?",
        "helper_text": "Neither answer is better.",
        "options": [
            opt("unsolved", "Figure out something nobody has solved yet", [("value_discovery", 1), ("investigative", Decimal("0.5"))],
                description="The thrill of finding out."),
            opt("improve", "Make something people already use work better", [("value_practical", 1), ("realistic", Decimal("0.5"))],
                description="The satisfaction of fixing it."),
        ],
    },
]


class Command(BaseCommand):
    help = "Seed the demo Discovery assessment v2 (mixed formats, hidden mappings)."

    @transaction.atomic
    def handle(self, *args, **options):
        signals = {}
        for key, (label, category) in SIGNALS.items():
            signals[key], _ = Signal.objects.update_or_create(
                key=key,
                defaults={
                    "label": label,
                    "category": category,
                    "is_active": True,
                    "translations": i18n.signal_translations(key),
                },
            )

        Assessment.objects.filter(slug__in=LEGACY_SLUGS).update(is_active=False)
        assessment, _ = Assessment.objects.update_or_create(
            slug=SLUG,
            defaults={
                "title": "Discovery Assessment",
                "description": "Ten short moments about what you enjoy, how you think and what you've tried.",
                "is_active": True,
                "translations": i18n.ASSESSMENT,
            },
        )
        section, _ = AssessmentSection.objects.update_or_create(
            assessment=assessment,
            slug="discovery",
            defaults={"title": "Discovery", "order": 0, "translations": i18n.SECTION},
        )

        for order, spec in enumerate(QUESTIONS):
            question, _ = Question.objects.update_or_create(
                section=section,
                order=order,
                defaults={
                    "type": spec["type"],
                    "prompt": spec["prompt"],
                    "helper_text": spec["helper_text"],
                    "content": spec.get("content", {}),
                    "is_active": True,
                    "translations": i18n.question_translations(order),
                },
            )
            keep = []
            for o_order, o in enumerate(spec["options"]):
                option, _ = QuestionOption.objects.update_or_create(
                    question=question,
                    value=o["value"],
                    defaults={
                        "label": o["label"],
                        "description": o["description"],
                        "image": o["image"],
                        "content": o["content"],
                        "icon": "",
                        "order": o_order,
                        "translations": i18n.option_translations(order, o["value"]),
                    },
                )
                keep.append(option.id)
                ResponseSignalMap.objects.filter(option=option).delete()
                ResponseSignalMap.objects.bulk_create(
                    ResponseSignalMap(option=option, signal=signals[key], weight=Decimal(w)) for key, w in o["maps"]
                )
            question.options.exclude(id__in=keep).delete()
        Question.objects.filter(section=section, order__gte=len(QUESTIONS)).update(is_active=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded '{assessment.title}' with {len(QUESTIONS)} questions and {len(SIGNALS)} signals."
            )
        )
