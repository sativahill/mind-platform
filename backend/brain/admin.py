from django.contrib import admin

from .models import Brain


@admin.register(Brain)
class BrainAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "updated_at")
    search_fields = ("user__email",)