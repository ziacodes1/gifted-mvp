"""Assessment content versioning (POC-level, deliberately simple).

Rules
- An assessment version is *locked* as soon as any learner has a session for it: its questions,
  options and signal mappings become read-only (Django admin enforces this).
- To change content, an admin clones the version into a new, inactive draft
  (`create_new_version`), edits the draft, then publishes it (`publish_version`), which activates
  it and deactivates the previous version. New sessions then use the new version.
- Old sessions keep pointing at the version they took (FK + `assessment_version`), carry the
  `scoring_version` they were scored with, and store a `result_snapshot`, so they are never
  re-interpreted.
- Scoring semantics are code (`scoring.SCORING_VERSION`); changing them means bumping that
  constant, not editing content.
"""
from __future__ import annotations

import re

from django.db import transaction

from apps.questions.models import Question, QuestionOption
from apps.signals.models import ResponseSignalMap

from .models import Assessment


def family_slug(assessment: Assessment) -> str:
    return re.sub(r"-v\d+$", "", assessment.slug)


def version_chain(assessment: Assessment) -> list[Assessment]:
    """All versions of the same assessment family (by slug prefix), oldest first."""
    base = family_slug(assessment)
    same = Assessment.objects.filter(slug__regex=rf"^{re.escape(base)}(-v\d+)?$")
    return sorted(same, key=lambda a: a.version)


@transaction.atomic
def create_new_version(source: Assessment) -> Assessment:
    """Deep-copy sections, questions, options and signal mappings into an inactive draft."""
    latest = max(a.version for a in version_chain(source))
    new = Assessment.objects.create(
        title=source.title,
        slug=f"{family_slug(source)}-v{latest + 1}",
        description=source.description,
        is_active=False,
        translations=source.translations,
        version=latest + 1,
        previous_version=source,
    )
    for section in source.sections.all():
        old_section_id = section.id
        section.pk = None
        section.assessment = new
        section.save()
        for q in Question.objects.filter(section_id=old_section_id):
            options = list(q.options.all())
            q.pk = None
            q.section = section
            q.save()
            for opt in options:
                maps = list(ResponseSignalMap.objects.filter(option=opt))
                opt.pk = None
                opt.question = q
                opt.save()
                for m in maps:
                    m.pk = None
                    m.option = opt
                    m.save()
    return new


@transaction.atomic
def publish_version(assessment: Assessment) -> None:
    """Make this version the one learners get; deactivate the other versions of the family."""
    for other in version_chain(assessment):
        if other.pk != assessment.pk and other.is_active:
            other.is_active = False
            other.save(update_fields=["is_active"])
    assessment.is_active = True
    assessment.save(update_fields=["is_active"])


def assessment_of(obj) -> Assessment | None:
    """The assessment a content row belongs to (for admin lock checks)."""
    if isinstance(obj, Assessment):
        return obj
    if isinstance(obj, Question):
        return obj.section.assessment
    if isinstance(obj, QuestionOption):
        return obj.question.section.assessment
    if isinstance(obj, ResponseSignalMap):
        return obj.option.question.section.assessment
    section = getattr(obj, "assessment", None)
    return section if isinstance(section, Assessment) else None
