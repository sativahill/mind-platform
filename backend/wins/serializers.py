from django.utils import timezone
from rest_framework import serializers

from .models import Win


class WinSerializer(serializers.ModelSerializer):
    source_label = serializers.CharField(
        source="get_source_display",
        read_only=True,
    )

    size_label = serializers.CharField(
        source="get_size_display",
        read_only=True,
    )

    class Meta:
        model = Win

        fields = (
            "id",
            "title",
            "description",
            "date",
            "size",
            "size_label",
            "source",
            "source_label",
            "source_id",
            "event_key",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "source",
            "source_label",
            "source_id",
            "event_key",
            "created_at",
            "updated_at",
        )

    def validate_title(self, value):
        title = value.strip()

        if not title:
            raise serializers.ValidationError(
                "Win title cannot be empty."
            )

        return title

    def validate_description(self, value):
        return value.strip()

    def validate_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError(
                "A win cannot be dated in the future."
            )

        return value

    def validate_size(self, value):
        valid_sizes = {
            Win.SMALL,
            Win.MEDIUM,
            Win.LARGE,
        }

        if value not in valid_sizes:
            raise serializers.ValidationError(
                "Choose small, medium or large."
            )

        return value