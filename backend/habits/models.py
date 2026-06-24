from django.conf import settings
from django.db import models


class Habit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="habits",
    )

    title = models.CharField(
        max_length=255,
    )

    trigger = models.CharField(
        max_length=255,
    )

    action = models.CharField(
        max_length=255,
    )

    reward = models.CharField(
        max_length=255,
        blank=True,
    )

    streak = models.PositiveIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title
    
class HabitCompletion(models.Model):
    habit = models.ForeignKey(
        Habit,
        on_delete=models.CASCADE,
        related_name="completions",
    )

    completed_at = models.DateField()

    class Meta:
        ordering = ["-completed_at"]

    def __str__(self):
        return (
            f"{self.habit.title} - "
            f"{self.completed_at}"
        )