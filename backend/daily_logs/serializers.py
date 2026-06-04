from rest_framework import serializers

from .models import DailyLog


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
        user = self.context["request"].user

        if DailyLog.objects.filter(
            user=user,
            date=value,
        ).exists():
            raise serializers.ValidationError(
                "Запись за эту дату уже существует."
            )

        return value