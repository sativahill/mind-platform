from datetime import timedelta

from django.utils import timezone

from rest_framework import serializers

from .models import Habit, HabitCompletion


class HabitDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    status = serializers.CharField()


class HabitSerializer(
    serializers.ModelSerializer
):
    completed_today = serializers.SerializerMethodField()
    today_status = serializers.SerializerMethodField()
    consecutive_misses = serializers.SerializerMethodField()
    recent_days = serializers.SerializerMethodField()

    class Meta:
        model = Habit

        fields = (
            "id",
            "title",
            "trigger",
            "action",
            "reward",
            "streak",
            "status",
            "completed_today",
            "today_status",
            "consecutive_misses",
            "recent_days",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "streak",
            "completed_today",
            "today_status",
            "consecutive_misses",
            "recent_days",
            "created_at",
            "updated_at",
        )

    def get_completed_today(
        self,
        habit,
    ):
        return habit.completed_today

    def get_today_status(
        self,
        habit,
    ):
        return habit.today_status

    def get_consecutive_misses(
        self,
        habit,
    ):
        return habit.consecutive_misses()

    def get_recent_days(
        self,
        habit,
    ):
        """
        Return the last 7 calendar days, including today.

        Each day always has one of:
        - completed
        - missed
        - pending

        Missing database records are treated as pending here.
        The backend does not automatically convert old empty days
        into missed records.
        """
        today = timezone.localdate()
        start_date = (
            today
            - timedelta(days=6)
        )

        completions = {
            completion.completed_at:
                completion.status
            for completion in (
                habit.completions
                .filter(
                    completed_at__gte=start_date,
                    completed_at__lte=today,
                )
                .only(
                    "completed_at",
                    "status",
                )
            )
        }

        days = []

        for offset in range(7):
            current_date = (
                start_date
                + timedelta(days=offset)
            )

            days.append(
                {
                    "date": current_date,
                    "status": completions.get(
                        current_date,
                        "pending",
                    ),
                }
            )

        return HabitDaySerializer(
            days,
            many=True,
        ).data

    def validate_title(
        self,
        value,
    ):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Habit title cannot be empty."
            )

        return value

    def validate_trigger(
        self,
        value,
    ):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Trigger cannot be empty."
            )

        return value

    def validate_action(
        self,
        value,
    ):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Action cannot be empty."
            )

        return value

    def validate_reward(
        self,
        value,
    ):
        return value.strip()