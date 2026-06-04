from django.conf import settings
from django.db import models

class Win(models.Model):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

    SIZE_CHOICES = [
        (SMALL, "Small"),
        (MEDIUM, "Medium"),
        (LARGE, "Large"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wins",
    )

    title = models.CharField(
        max_length=255,
    )

    size = models.CharField(
        max_length=10,
        choices=SIZE_CHOICES,
        default=SMALL,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return self.title