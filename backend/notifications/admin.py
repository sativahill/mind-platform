from django.contrib import admin

from .models import Notification, NotificationSettings


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "morning_enabled",
        "evening_enabled",
        "day_off",
    )

    search_fields = (
        "user__email",
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "notification_type",
        "user",
        "is_read",
        "created_at",
    )

    list_filter = (
        "notification_type",
        "is_read",
    )

    search_fields = (
        "title",
        "message",
        "user__email",
    )
