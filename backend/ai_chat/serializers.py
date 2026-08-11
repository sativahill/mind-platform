from rest_framework import serializers

from .models import Chat, Message


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat

        fields = (
            "id",
            "title",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def validate_title(self, value):
        title = value.strip()

        if not title:
            raise serializers.ValidationError(
                "Chat title cannot be empty."
            )

        return title


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message

        fields = (
            "id",
            "role",
            "content",
            "created_at",
        )

        read_only_fields = (
            "id",
            "role",
            "created_at",
        )

    def validate_content(self, value):
        content = value.strip()

        if not content:
            raise serializers.ValidationError(
                "Message cannot be empty."
            )

        return content