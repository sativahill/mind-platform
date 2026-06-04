from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import User
from .models import Brain


@receiver(post_save, sender=User)
def create_user_brain(sender, instance, created, **kwargs):
    if created:
        Brain.objects.create(
            user=instance,
            data={
                "user": {},
                "goals": [],
                "wins": [],
                "context": {},
                "patterns": {}
            }
        )