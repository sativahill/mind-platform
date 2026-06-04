from django.contrib import admin

from .models import Win


@admin.register(Win)
class WinAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "size",
        "user",
        "created_at",
    )

    list_filter = (
        "size",
        "created_at",
    )

    search_fields = (
        "title",
        "user__email",
    )

    ordering = (
        "-created_at",
    )