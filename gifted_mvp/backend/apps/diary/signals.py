from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import DiaryAttachment


@receiver(post_delete, sender=DiaryAttachment)
def remove_photo_file(sender, instance, **kwargs):
    # Runs for direct deletes and for cascades (entry deleted, learner reset).
    if instance.image:
        instance.image.delete(save=False)
