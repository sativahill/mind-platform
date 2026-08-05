from django.contrib import admin

from .models import (
    BoardTask,
    BoardTaskDependency,
)


class BoardTaskDependencyInline(
    admin.TabularInline
):
    model = BoardTaskDependency
    fk_name = "task"

    extra = 0

    autocomplete_fields = (
        "depends_on",
    )

    readonly_fields = (
        "created_at",
    )


@admin.register(BoardTask)
class BoardTaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "goal",
        "status",
        "priority",
        "importance",
        "is_blocked_display",
        "due_date",
        "sort_order",
        "source",
        "updated_at",
    )

    list_filter = (
        "status",
        "priority",
        "importance",
        "source",
        "due_date",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "title",
        "description",
        "goal__title",
        "goal__user__email",
    )

    autocomplete_fields = (
        "goal",
    )

    readonly_fields = (
        "completed_at",
        "created_at",
        "updated_at",
        "is_blocked_display",
    )

    fieldsets = (
        (
            "Task",
            {
                "fields": (
                    "goal",
                    "title",
                    "description",
                    "status",
                )
            },
        ),
        (
            "Planning",
            {
                "fields": (
                    "priority",
                    "importance",
                    "due_date",
                    "source",
                )
            },
        ),
        (
            "Board position",
            {
                "fields": (
                    "position_x",
                    "position_y",
                    "sort_order",
                )
            },
        ),
        (
            "State",
            {
                "fields": (
                    "is_blocked_display",
                    "completed_at",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    inlines = (
        BoardTaskDependencyInline,
    )

    ordering = (
        "sort_order",
        "created_at",
    )

    list_select_related = (
        "goal",
        "goal__user",
    )

    @admin.display(
        boolean=True,
        description="Blocked",
    )
    def is_blocked_display(
        self,
        task,
    ):
        return task.is_blocked


@admin.register(BoardTaskDependency)
class BoardTaskDependencyAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "task",
        "depends_on",
        "task_goal",
        "created_at",
    )

    search_fields = (
        "task__title",
        "depends_on__title",
        "task__goal__title",
        "task__goal__user__email",
    )

    autocomplete_fields = (
        "task",
        "depends_on",
    )

    readonly_fields = (
        "created_at",
    )

    list_select_related = (
        "task",
        "task__goal",
        "depends_on",
    )

    ordering = (
        "-created_at",
    )

    @admin.display(
        description="Goal",
    )
    def task_goal(
        self,
        dependency,
    ):
        return dependency.task.goal