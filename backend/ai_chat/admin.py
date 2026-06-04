from django.contrib import admin

from .models import Chat, Message


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "user",
        "updated_at",
    )

    search_fields = (
        "title",
        "user__email",
    )

    ordering = (
        "-updated_at",
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "chat",
        "role",
        "created_at",
    )

    list_filter = (
        "role",
    )

    search_fields = (
        "content",
    )

    ordering = (
        "created_at",
    )