from django.contrib import admin

from .models import Goal


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "status",
        "progress",
        "target_date",
        "completed_at",
        "user",
        "updated_at",
    )

    list_filter = (
        "status",
        "target_date",
        "completed_at",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "why_it_matters",
        "previous_obstacles",
        "user__username",
        "user__email",
    )

    readonly_fields = (
        "progress",
        "completed_at",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Goal",
            {
                "fields": (
                    "user",
                    "title",
                    "description",
                    "why_it_matters",
                    "previous_obstacles",
                    "target_date",
                )
            },
        ),
        (
            "Progress",
            {
                "fields": (
                    "status",
                    "progress",
                    "completed_at",
                )
            },
        ),
        (
            "System",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    ordering = (
        "-updated_at",
    )

    list_select_related = (
        "user",
    )