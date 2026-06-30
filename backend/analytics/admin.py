from django.contrib import admin

from .models import AnalyticsMessage, AnalyticsReport


@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "week_start",
        "week_end",
        "created_at",
    )

    search_fields = (
        "user__email",
        "content",
    )


@admin.register(AnalyticsMessage)
class AnalyticsMessageAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "role",
        "created_at",
    )

    list_filter = (
        "role",
    )

    search_fields = (
        "user__email",
        "content",
    )
