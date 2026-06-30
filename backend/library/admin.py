from django.contrib import admin

from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "progress",
        "is_completed",
        "created_at",
    )

    list_filter = (
        "is_completed",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "user__email",
    )
