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