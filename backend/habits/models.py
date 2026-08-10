from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Habit(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

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

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "status",
            "-updated_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "user",
                    "status",
                ],
                name="habit_user_status_idx",
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def completed_today(self):
        today = timezone.localdate()

        return self.completions.filter(
            completed_at=today,
            status=HabitCompletion.Status.COMPLETED,
        ).exists()

    @property
    def missed_today(self):
        today = timezone.localdate()

        return self.completions.filter(
            completed_at=today,
            status=HabitCompletion.Status.MISSED,
        ).exists()

    @property
    def today_status(self):
        if self.completed_today:
            return HabitCompletion.Status.COMPLETED

        if self.missed_today:
            return HabitCompletion.Status.MISSED

        return "pending"

    def calculate_streak(self):
        """
        Current consecutive completion streak.

        If today is still pending, a streak ending yesterday
        remains active.

        Examples:

        Mon ✓ Tue ✓ Wed pending
        -> streak = 2

        Mon ✓ Tue ✓ Wed missed
        -> streak = 0

        Mon ✓ Tue missed Wed ✓
        -> streak = 1
        """
        today = timezone.localdate()

        records = {
            record.completed_at: record.status
            for record in self.completions.filter(
                completed_at__lte=today,
            ).only(
                "completed_at",
                "status",
            )
        }

        today_status = records.get(today)

        if (
            today_status
            == HabitCompletion.Status.MISSED
        ):
            return 0

        if (
            today_status
            == HabitCompletion.Status.COMPLETED
        ):
            cursor = today
        else:
            cursor = today - timedelta(days=1)

        streak = 0

        while (
            records.get(cursor)
            == HabitCompletion.Status.COMPLETED
        ):
            streak += 1
            cursor -= timedelta(days=1)

        return streak

    def refresh_streak(self, save=True):
        new_streak = self.calculate_streak()

        if self.streak != new_streak:
            self.streak = new_streak

            if save:
                self.save(
                    update_fields=[
                        "streak",
                        "updated_at",
                    ]
                )

        return self.streak

    def consecutive_misses(self):
        """
        Number of explicit consecutive missed days.

        Pending today is ignored, so during the current day
        yesterday's miss chain is still visible.
        """
        today = timezone.localdate()

        records = {
            record.completed_at: record.status
            for record in self.completions.filter(
                completed_at__lte=today,
            ).only(
                "completed_at",
                "status",
            )
        }

        today_status = records.get(today)

        if (
            today_status
            == HabitCompletion.Status.MISSED
        ):
            cursor = today

        elif today_status is None:
            cursor = today - timedelta(days=1)

        else:
            return 0

        missed = 0

        while (
            records.get(cursor)
            == HabitCompletion.Status.MISSED
        ):
            missed += 1
            cursor -= timedelta(days=1)

        return missed


class HabitCompletion(models.Model):
    class Status(models.TextChoices):
        COMPLETED = "completed", "Completed"
        MISSED = "missed", "Missed"

    habit = models.ForeignKey(
        Habit,
        on_delete=models.CASCADE,
        related_name="completions",
    )

    completed_at = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.COMPLETED,
    )

    class Meta:
        ordering = [
            "-completed_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "habit",
                    "completed_at",
                ],
                name="unique_habit_day",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "habit",
                    "-completed_at",
                ],
                name="habit_completion_date_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.habit.title} - "
            f"{self.completed_at} - "
            f"{self.status}"
        )