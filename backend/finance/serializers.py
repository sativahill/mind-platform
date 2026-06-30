from rest_framework import serializers

from .models import FinanceGoal, FinanceTransaction


class FinanceGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceGoal

        fields = (
            "id",
            "title",
            "target_amount",
            "current_amount",
            "deadline",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )


class FinanceTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceTransaction

        fields = (
            "id",
            "goal",
            "amount",
            "note",
            "created_at",
        )

        read_only_fields = (
            "id",
            "goal",
            "created_at",
        )
