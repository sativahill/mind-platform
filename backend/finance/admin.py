from django.contrib import admin

from .models import FinanceGoal, FinanceTransaction


@admin.register(FinanceGoal)
class FinanceGoalAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "target_amount",
        "current_amount",
        "deadline",
    )

    search_fields = (
        "title",
        "user__email",
    )


@admin.register(FinanceTransaction)
class FinanceTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "goal",
        "amount",
        "created_at",
    )

    search_fields = (
        "goal__title",
        "note",
    )
