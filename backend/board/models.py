from django.db import models
from goals.models import Goal

class BoardTask(models.Model):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

    STATUS_CHOICES = [
        (TODO, "To Do"),
        (IN_PROGRESS, "In Progress"),
        (DONE, "Done"),
    ]

    goal = models.ForeignKey(
        Goal,
        on_delete=models.CASCADE,
        related_name="tasks",
    )

    title = models.CharField(
        max_length=255,
    )

    description = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=TODO,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["created_at"]
    
    def __str__(self):
        return self.title