from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Win(models.Model):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

    SIZE_CHOICES = [
        (SMALL, "Small"),
        (MEDIUM, "Medium"),
        (LARGE, "Large"),
    ]

    MANUAL = "manual"
    DAILY_LOG = "daily_log"
    GOAL = "goal"
    BOARD = "board"
    HABIT = "habit"
    LIBRARY = "library"
    FINANCE = "finance"
    PROGRESS_PHOTO = "progress_photo"

    SOURCE_CHOICES = [
        (MANUAL, "Manual"),
        (DAILY_LOG, "Daily Log"),
        (GOAL, "Goal"),
        (BOARD, "Board"),
        (HABIT, "Habit"),
        (LIBRARY, "Library"),
        (FINANCE, "Finance"),
        (PROGRESS_PHOTO, "Progress Photo"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wins",
    )

    title = models.CharField(
        max_length=255,
    )

    description = models.TextField(
        blank=True,
    )

    date = models.DateField(
        default=timezone.localdate,
    )

    size = models.CharField(
        max_length=10,
        choices=SIZE_CHOICES,
        default=SMALL,
    )

    source = models.CharField(
        max_length=30,
        choices=SOURCE_CHOICES,
        default=MANUAL,
    )

    source_id = models.CharField(
        max_length=100,
        blank=True,
    )

    event_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-date",
            "-created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "event_key",
                ],
                condition=Q(
                    event_key__isnull=False
                ),
                name=(
                    "unique_win_event_per_user"
                ),
            ),
        ]

    def __str__(self):
        return self.title