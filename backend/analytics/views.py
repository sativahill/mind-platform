from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_chat.services import generate_ai_response

from .models import AnalyticsMessage, AnalyticsReport
from .serializers import (
    AnalyticsMessageSerializer,
    AnalyticsReportSerializer,
)


class AnalyticsReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reports = AnalyticsReport.objects.filter(
            user=request.user
        )

        serializer = AnalyticsReportSerializer(
            reports,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = AnalyticsReportSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        report = AnalyticsReport.objects.create(
            user=request.user,
            week_start=serializer.validated_data["week_start"],
            week_end=serializer.validated_data["week_end"],
            content=serializer.validated_data["content"],
        )

        return Response(
            AnalyticsReportSerializer(report).data,
            status=201,
        )


class AnalyticsMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        messages = AnalyticsMessage.objects.filter(
            user=request.user
        )

        serializer = AnalyticsMessageSerializer(
            messages,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = AnalyticsMessageSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user_message = AnalyticsMessage.objects.create(
            user=request.user,
            role=AnalyticsMessage.USER,
            content=serializer.validated_data["content"],
        )

        messages = AnalyticsMessage.objects.filter(
            user=request.user
        ).order_by("created_at")[:20]

        ai_response = generate_ai_response(
            request.user.brain,
            user_message.content,
            messages,
        )

        assistant_message = AnalyticsMessage.objects.create(
            user=request.user,
            role=AnalyticsMessage.ASSISTANT,
            content=ai_response,
        )

        return Response(
            AnalyticsMessageSerializer(assistant_message).data,
            status=201,
        )
