from django.contrib import admin

from .models import BoardTask


@admin.register(BoardTask)
class BoardTaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "status",
        "goal",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
    )