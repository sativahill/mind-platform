from django.conf import settings
from django.db import models


class FinanceGoal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="finance_goals",
    )

    title = models.CharField(
        max_length=255,
    )

    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    current_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    deadline = models.DateField(
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
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class FinanceTransaction(models.Model):
    goal = models.ForeignKey(
        FinanceGoal,
        on_delete=models.CASCADE,
        related_name="transactions",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    note = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.goal.title} - {self.amount}"
