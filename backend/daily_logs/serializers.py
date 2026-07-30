from django.utils import timezone
from rest_framework import serializers

from .models import (
    DailyLog,
    DailyLogSuggestion,
)


class DailyLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyLog

        fields = (
            "id",
            "date",
            "content",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def validate_date(self, value):
        request = self.context["request"]
        user = request.user

        if value > timezone.localdate():
            raise serializers.ValidationError(
                "You cannot create a Daily Log for a future date."
            )

        existing_logs = DailyLog.objects.filter(
            user=user,
            date=value,
        )

        if self.instance is not None:
            existing_logs = existing_logs.exclude(
                pk=self.instance.pk
            )

        if existing_logs.exists():
            raise serializers.ValidationError(
                "A Daily Log for this date already exists."
            )

        return value

    def validate_content(self, value):
        cleaned_value = value.strip()

        if not cleaned_value:
            raise serializers.ValidationError(
                "Daily Log content cannot be empty."
            )

        return cleaned_value


class DailyLogSuggestionSerializer(serializers.ModelSerializer):
    type_label = serializers.CharField(
        source="get_suggestion_type_display",
        read_only=True,
    )

    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    size_label = serializers.CharField(
        source="get_size_display",
        read_only=True,
    )

    class Meta:
        model = DailyLogSuggestion

        fields = (
            "id",
            "daily_log",
            "suggestion_type",
            "type_label",
            "title",
            "description",
            "size",
            "size_label",
            "status",
            "status_label",
            "suggestion_key",
            "resolved_at",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "daily_log",
            "suggestion_type",
            "type_label",
            "status",
            "status_label",
            "suggestion_key",
            "resolved_at",
            "created_at",
            "updated_at",
        )

    def validate_title(self, value):
        cleaned_value = value.strip()

        if not cleaned_value:
            raise serializers.ValidationError(
                "Suggestion title cannot be empty."
            )

        return cleaned_value

    def validate_description(self, value):
        return value.strip()

    def validate_size(self, value):
        allowed_sizes = {
            DailyLogSuggestion.SIZE_SMALL,
            DailyLogSuggestion.SIZE_MEDIUM,
            DailyLogSuggestion.SIZE_LARGE,
        }

        if value not in allowed_sizes:
            raise serializers.ValidationError(
                "Invalid suggestion size."
            )

        return value