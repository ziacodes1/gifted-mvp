"""Account lifecycle."""
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken


def delete_account(user) -> None:
    """Hard delete. Every learner-owned row references the user with on_delete=CASCADE
    (sessions, signals, evidence, Passport, missions, diary, Companion, engagement, today),
    and diary photo files are removed by the diary post_delete signal. Outstanding tokens go
    too, so no refresh token of the deleted account keeps working. Seeded content and other
    learners are untouched."""
    OutstandingToken.objects.filter(user=user).delete()
    user.delete()
