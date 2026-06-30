from django.conf import settings
from django.db import models


class NotificationSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_settings",
    )

    morning_enabled = models.BooleanField(
        default=True,
    )

    evening_enabled = models.BooleanField(
        default=True,
    )

    day_off = models.CharField(
        max_length=20,
        blank=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.user.email} notifications"


class Notification(models.Model):
    MORNING = "morning"
    EVENING = "evening"
    STREAK = "streak"

    TYPE_CHOICES = [
        (MORNING, "Morning"),
        (EVENING, "Evening"),
        (STREAK, "Streak"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
    )

    title = models.CharField(
        max_length=255,
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
