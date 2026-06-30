from rest_framework import serializers

from .models import ProgressPhoto


class ProgressPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressPhoto

        fields = (
            "id",
            "photo",
            "date",
            "metrics",
            "ai_analysis",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )
