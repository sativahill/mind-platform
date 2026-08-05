from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
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

    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_CRITICAL = "critical"

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_CRITICAL, "Critical"),
    ]

    IMPORTANCE_SMALL = "small"
    IMPORTANCE_MEDIUM = "medium"
    IMPORTANCE_LARGE = "large"

    IMPORTANCE_CHOICES = [
        (IMPORTANCE_SMALL, "Small"),
        (IMPORTANCE_MEDIUM, "Medium"),
        (IMPORTANCE_LARGE, "Large"),
    ]

    SOURCE_MANUAL = "manual"
    SOURCE_GOAL_AI = "goal_ai"
    SOURCE_DAILY_LOG = "daily_log"

    SOURCE_CHOICES = [
        (SOURCE_MANUAL, "Manual"),
        (SOURCE_GOAL_AI, "Goal AI"),
        (SOURCE_DAILY_LOG, "Daily Log"),
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

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
    )

    importance = models.CharField(
        max_length=20,
        choices=IMPORTANCE_CHOICES,
        default=IMPORTANCE_SMALL,
    )

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default=SOURCE_MANUAL,
    )

    due_date = models.DateField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    position_x = models.PositiveIntegerField(
        default=5000,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10000),
        ],
        help_text=(
            "Horizontal position inside the current Board zone, "
            "stored as a normalized value from 0 to 10000."
        ),
    )

    position_y = models.PositiveIntegerField(
        default=5000,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10000),
        ],
        help_text=(
            "Vertical position inside the current Board zone, "
            "stored as a normalized value from 0 to 10000."
        ),
    )

    sort_order = models.PositiveIntegerField(
        default=0,
    )

    dependencies = models.ManyToManyField(
        "self",
        through="BoardTaskDependency",
        through_fields=(
            "task",
            "depends_on",
        ),
        symmetrical=False,
        related_name="dependent_tasks",
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
            "sort_order",
            "created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "goal",
                    "status",
                    "sort_order",
                ],
                name="board_goal_status_order_idx",
            ),
            models.Index(
                fields=[
                    "goal",
                    "due_date",
                ],
                name="board_goal_due_date_idx",
            ),
            models.Index(
                fields=[
                    "status",
                    "priority",
                ],
                name="board_status_priority_idx",
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def is_blocked(self):
        if not self.pk:
            return False

        return self.dependencies.exclude(
            status=self.DONE,
        ).exists()


class BoardTaskDependency(models.Model):
    task = models.ForeignKey(
        BoardTask,
        on_delete=models.CASCADE,
        related_name="dependency_links",
    )

    depends_on = models.ForeignKey(
        BoardTask,
        on_delete=models.CASCADE,
        related_name="dependent_links",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "task",
                    "depends_on",
                ],
                name="unique_board_task_dependency",
            ),
            models.CheckConstraint(
                condition=~models.Q(
                    task=models.F("depends_on"),
                ),
                name="board_task_cannot_depend_on_itself",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "task",
                    "depends_on",
                ],
                name="board_dependency_pair_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.task.title} depends on "
            f"{self.depends_on.title}"
        )