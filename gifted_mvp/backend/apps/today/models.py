"""Today: the learner's daily Spark and nudge read-state. Tiny on purpose.

`DailySpark` pins the day's card so refreshing never reshuffles it; it only changes when the
learner completes the action it asked for. No content is stored — keys and dates only.
"""
from django.conf import settings
from django.db import models


class SparkStatus(models.TextChoices):
    NEW = "NEW", "New"
    DONE = "DONE", "Done"
    DISMISSED = "DISMISSED", "Set aside for today"


class DailySpark(models.Model):
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_sparks")
    day = models.DateField()  # learner-local (engagement ACTIVITY_TIME_ZONE)
    spark_key = models.CharField(max_length=40)
    status = models.CharField(max_length=10, choices=SparkStatus.choices, default=SparkStatus.NEW)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "today_daily_spark"
        constraints = [models.UniqueConstraint(fields=["learner", "day"], name="uniq_daily_spark")]


class NudgeState(models.Model):
    learner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="nudge_state")
    seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "today_nudge_state"
