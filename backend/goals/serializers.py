from rest_framework import serializers

from .models import Goal


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal

        fields = (
            "id",
            "title",
            "description",
            "why_it_matters",
            "previous_obstacles",
            "target_date",
            "status",
            "progress",
            "completed_at",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "progress",
            "completed_at",
            "created_at",
            "updated_at",
        )

    def validate_title(self, value):
        title = value.strip()

        if not title:
            raise serializers.ValidationError(
                "Goal title cannot be empty."
            )

        return title

    def validate_description(self, value):
        return value.strip()

    def validate_why_it_matters(self, value):
        return value.strip()

    def validate_previous_obstacles(self, value):
        return value.strip()

    def validate(self, attrs):
        status = attrs.get(
            "status",
            getattr(self.instance, "status", Goal.ACTIVE),
        )

        if status == Goal.COMPLETED:
            raise serializers.ValidationError(
                {
                    "status": (
                        "A goal cannot be marked as completed manually. "
                        "Completion is controlled by goal progress."
                    )
                }
            )

        return attrs