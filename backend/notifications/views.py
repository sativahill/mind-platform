from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, NotificationSettings
from .serializers import (
    NotificationSerializer,
    NotificationSettingsSerializer,
)


class NotificationSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        settings, created = NotificationSettings.objects.get_or_create(
            user=request.user
        )

        serializer = NotificationSettingsSerializer(settings)

        return Response(serializer.data)

    def patch(self, request):
        settings, created = NotificationSettings.objects.get_or_create(
            user=request.user
        )

        serializer = NotificationSettingsSerializer(
            settings,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(serializer.data)


class NotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(
            user=request.user
        )

        serializer = NotificationSerializer(
            notifications,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = NotificationSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        notification = Notification.objects.create(
            user=request.user,
            notification_type=serializer.validated_data[
                "notification_type"
            ],
            title=serializer.validated_data["title"],
            message=serializer.validated_data["message"],
            is_read=serializer.validated_data.get(
                "is_read",
                False,
            ),
        )

        return Response(
            NotificationSerializer(notification).data,
            status=201,
        )


class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id):
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            user=request.user,
        )

        serializer = NotificationSerializer(
            notification,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(serializer.data)
