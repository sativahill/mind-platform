from django.contrib import admin

from .models import DailyLog


@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "date",
        "created_at",
    )

    list_filter = (
        "date",
        "created_at",
    )

    search_fields = (
        "user__email",
        "content",
    )

    ordering = (
        "-date",
        "-created_at",
    )