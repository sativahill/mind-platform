from django.utils import timezone
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