from django.conf import settings
from django.db import models


class DailyLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_logs",
    )

    date = models.DateField()

    content = models.TextField()

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
                    "date",
                ],
                name="unique_daily_log_per_user_date",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.email} - "
            f"{self.date}"
        )


class DailyLogSuggestion(models.Model):
    TYPE_WIN = "win"
    TYPE_GOAL = "goal"
    TYPE_BOOK = "book"
    TYPE_HABIT = "habit"
    TYPE_CONTEXT = "context"

    TYPE_CHOICES = [
        (
            TYPE_WIN,
            "Win",
        ),
        (
            TYPE_GOAL,
            "Goal",
        ),
        (
            TYPE_BOOK,
            "Book",
        ),
        (
            TYPE_HABIT,
            "Habit",
        ),
        (
            TYPE_CONTEXT,
            "Context",
        ),
    ]

    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_DISMISSED = "dismissed"

    STATUS_CHOICES = [
        (
            STATUS_PENDING,
            "Pending",
        ),
        (
            STATUS_ACCEPTED,
            "Accepted",
        ),
        (
            STATUS_DISMISSED,
            "Dismissed",
        ),
    ]

    SIZE_SMALL = "small"
    SIZE_MEDIUM = "medium"
    SIZE_LARGE = "large"

    SIZE_CHOICES = [
        (
            SIZE_SMALL,
            "Small",
        ),
        (
            SIZE_MEDIUM,
            "Medium",
        ),
        (
            SIZE_LARGE,
            "Large",
        ),
    ]

    daily_log = models.ForeignKey(
        DailyLog,
        on_delete=models.CASCADE,
        related_name="suggestions",
    )

    suggestion_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_WIN,
    )

    title = models.CharField(
        max_length=255,
    )

    description = models.TextField(
        blank=True,
    )

    size = models.CharField(
        max_length=10,
        choices=SIZE_CHOICES,
        default=SIZE_SMALL,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    suggestion_key = models.CharField(
        max_length=64,
    )

    resolved_at = models.DateTimeField(
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
            "created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "daily_log",
                    "suggestion_key",
                ],
                name="unique_suggestion_per_daily_log",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "daily_log",
                    "status",
                ],
                name="dlog_sugg_status_idx",
        ),
        models.Index(
            fields=[
                "suggestion_type",
                "status",
            ],
            name="sugg_type_status_idx",
        ),
    ]

    def __str__(self):
        return (
            f"{self.daily_log.date} - "
            f"{self.suggestion_type}: "
            f"{self.title}"
        )