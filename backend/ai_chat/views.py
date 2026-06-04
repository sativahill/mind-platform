from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer
from .services import generate_ai_response


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        chats = Chat.objects.filter(
            user=request.user
        )

        serializer = ChatSerializer(
            chats,
            many=True
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = ChatSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        chat = Chat.objects.create(
            user=request.user,
            title=serializer.validated_data["title"],
        )

        return Response(
            ChatSerializer(chat).data,
            status=201
        )


class MessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, chat_id):
        chat = get_object_or_404(
            Chat,
            id=chat_id,
            user=request.user,
        )

        messages = Message.objects.filter(
            chat=chat
        )

        serializer = MessageSerializer(
            messages,
            many=True
        )

        return Response(serializer.data)

    def post(self, request, chat_id):
        chat = get_object_or_404(
            Chat,
            id=chat_id,
            user=request.user,
        )

        serializer = MessageSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user_message = Message.objects.create(
            chat=chat,
            role="user",
            content=serializer.validated_data["content"],
        )

        messages = Message.objects.filter(
            chat=chat
        ).order_by("created_at")[:20]

        ai_response = generate_ai_response(
            request.user.brain,
            user_message.content,
            messages,
        )

        assistant_message = Message.objects.create(
            chat=chat,
            role="assistant",
            content=ai_response,
        )

        return Response(
            MessageSerializer(assistant_message).data,
            status=201,
        )