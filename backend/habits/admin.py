from django.contrib import admin

from .models import (
    Habit,
    HabitCompletion,
)


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "streak",
        "created_at",
    )

    search_fields = (
        "title",
        "trigger",
        "action",
    )


@admin.register(HabitCompletion)
class HabitCompletionAdmin(
    admin.ModelAdmin
):
    list_display = (
        "habit",
        "completed_at",
    )