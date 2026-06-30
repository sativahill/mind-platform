from rest_framework import serializers

from .models import AnalyticsMessage, AnalyticsReport


class AnalyticsReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsReport

        fields = (
            "id",
            "week_start",
            "week_end",
            "content",
            "created_at",
        )

        read_only_fields = (
            "id",
            "created_at",
        )


class AnalyticsMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsMessage

        fields = (
            "id",
            "role",
            "content",
            "created_at",
        )

        read_only_fields = (
            "id",
            "role",
            "created_at",
        )
