from django.conf import settings
from django.db import models


class Book(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="books",
    )

    title = models.CharField(
        max_length=255,
    )

    description = models.TextField(
        blank=True,
    )

    cover_url = models.URLField(
        blank=True,
    )

    progress = models.PositiveIntegerField(
        default=0,
    )

    quotes = models.JSONField(
        default=list,
        blank=True,
    )

    insights = models.JSONField(
        default=list,
        blank=True,
    )

    is_completed = models.BooleanField(
        default=False,
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
