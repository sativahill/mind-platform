from django.conf import settings
from django.db import models


class ProgressPhoto(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="progress_photos",
    )

    photo = models.FileField(
        upload_to="progress_photos/",
    )

    date = models.DateField()

    metrics = models.JSONField(
        default=dict,
        blank=True,
    )

    ai_analysis = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.date}"
