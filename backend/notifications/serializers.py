from rest_framework import serializers

from .models import Notification, NotificationSettings


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings

        fields = (
            "id",
            "morning_enabled",
            "evening_enabled",
            "day_off",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "updated_at",
        )


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification

        fields = (
            "id",
            "notification_type",
            "title",
            "message",
            "is_read",
            "created_at",
        )

        read_only_fields = (
            "id",
            "created_at",
        )
