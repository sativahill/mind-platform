from rest_framework import serializers

from .models import BoardTask


class BoardTaskSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = BoardTask

        fields = (
            "id",
            "goal",
            "title",
            "description",
            "status",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )