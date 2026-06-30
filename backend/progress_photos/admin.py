from django.contrib import admin

from .models import ProgressPhoto


@admin.register(ProgressPhoto)
class ProgressPhotoAdmin(admin.ModelAdmin):
    list_display = (
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
        "ai_analysis",
    )
