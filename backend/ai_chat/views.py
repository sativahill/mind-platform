from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Chat, Message
from .serializers import (
    ChatSerializer,
    MessageSerializer,
)
from .services import generate_ai_response


CHAT_HISTORY_LIMIT = 20


class ChatView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        chats = (
            Chat.objects
            .filter(
                user=request.user
            )
            .order_by(
                "-updated_at"
            )
        )

        serializer = ChatSerializer(
            chats,
            many=True,
        )

        return Response(
            serializer.data
        )

    def post(self, request):
        serializer = ChatSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        chat = Chat.objects.create(
            user=request.user,
            title=serializer.validated_data[
                "title"
            ],
        )

        return Response(
            ChatSerializer(
                chat
            ).data,
            status=201,
        )


class MessageView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        chat_id,
    ):
        chat = get_object_or_404(
            Chat,
            id=chat_id,
            user=request.user,
        )

        messages = (
            Message.objects
            .filter(
                chat=chat
            )
            .order_by(
                "created_at"
            )
        )

        serializer = (
            MessageSerializer(
                messages,
                many=True,
            )
        )

        return Response(
            serializer.data
        )

    def post(
        self,
        request,
        chat_id,
    ):
        chat = get_object_or_404(
            Chat,
            id=chat_id,
            user=request.user,
        )

        serializer = (
            MessageSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        user_message = (
            Message.objects.create(
                chat=chat,
                role=Message.USER,
                content=(
                    serializer
                    .validated_data[
                        "content"
                    ]
                ),
            )
        )

        previous_messages = list(
            Message.objects
            .filter(
                chat=chat,
            )
            .exclude(
                id=user_message.id
            )
            .order_by(
                "-created_at"
            )[
                :CHAT_HISTORY_LIMIT
            ]
        )

        previous_messages.reverse()

        conversation_messages = [
            *previous_messages,
            user_message,
        ]

        other_chat_titles = list(
            Chat.objects
            .filter(
                user=request.user,
            )
            .exclude(
                id=chat.id
            )
            .values_list(
                "title",
                flat=True,
            )
        )

        brain = getattr(
            request.user,
            "brain",
            None,
        )

        ai_response = (
            generate_ai_response(
                brain=brain,
                current_chat_title=(
                    chat.title
                ),
                other_chat_titles=(
                    other_chat_titles
                ),
                messages=(
                    conversation_messages
                ),
            )
        )

        assistant_message = (
            Message.objects.create(
                chat=chat,
                role=Message.ASSISTANT,
                content=ai_response,
            )
        )

        Chat.objects.filter(
            id=chat.id
        ).update(
            updated_at=timezone.now()
        )

        return Response(
            MessageSerializer(
                assistant_message
            ).data,
            status=201,
        )