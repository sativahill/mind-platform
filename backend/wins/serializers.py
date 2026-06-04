from rest_framework import serializers

from .models import Win


class WinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Win

        fields = (
            "id",
            "title",
            "size",
            "created_at",
        )

        read_only_fields = (
            "id",
            "created_at",
        )