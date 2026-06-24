from rest_framework import serializers

from .models import Habit


class HabitSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Habit

        fields = (
            "id",
            "title",
            "trigger",
            "action",
            "reward",
            "streak",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "streak",
            "created_at",
            "updated_at",
        )