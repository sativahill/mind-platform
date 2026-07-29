from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DailyLog
from .serializers import DailyLogSerializer
from .services import update_brain_from_daily_log


class DailyLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get_log(self, request):
        """
        Находит запись текущего пользователя.

        Поддерживает:
        /api/daily-logs/?id=12
        /api/daily-logs/?date=2026-07-29
        """
        log_id = request.query_params.get("id")
        log_date = request.query_params.get("date")

        if log_id:
            return get_object_or_404(
                DailyLog,
                id=log_id,
                user=request.user,
            )

        if log_date:
            return get_object_or_404(
                DailyLog,
                date=log_date,
                user=request.user,
            )

        return None

    def get(self, request):
        log = self.get_log(request)

        if log is not None:
            serializer = DailyLogSerializer(
                log,
                context={"request": request},
            )

            return Response(serializer.data)

        logs = DailyLog.objects.filter(
            user=request.user
        )

        serializer = DailyLogSerializer(
            logs,
            many=True,
            context={"request": request},
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = DailyLogSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(
            raise_exception=True
        )

        daily_log = serializer.save(
            user=request.user
        )

        update_brain_from_daily_log(
            daily_log
        )

        response_serializer = DailyLogSerializer(
            daily_log,
            context={"request": request},
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request):
        daily_log = self.get_log(request)

        if daily_log is None:
            return Response(
                {
                    "detail": (
                        "Provide the Daily Log id or date "
                        "in the query parameters."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DailyLogSerializer(
            daily_log,
            data=request.data,
            partial=True,
            context={"request": request},
        )

        serializer.is_valid(
            raise_exception=True
        )

        updated_log = serializer.save()

        update_brain_from_daily_log(
            updated_log
        )

        response_serializer = DailyLogSerializer(
            updated_log,
            context={"request": request},
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        daily_log = self.get_log(request)

        if daily_log is None:
            return Response(
                {
                    "detail": (
                        "Provide the Daily Log id or date "
                        "in the query parameters."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DailyLogSerializer(
            daily_log,
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(
            raise_exception=True
        )

        updated_log = serializer.save()

        update_brain_from_daily_log(
            updated_log
        )

        response_serializer = DailyLogSerializer(
            updated_log,
            context={"request": request},
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        daily_log = self.get_log(request)

        if daily_log is None:
            return Response(
                {
                    "detail": (
                        "Provide the Daily Log id or date "
                        "in the query parameters."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        daily_log.delete()

        self.sync_brain_after_delete(
            request.user
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    @staticmethod
    def sync_brain_after_delete(user):
        """
        После удаления текущего последнего лога
        обновляет Brain данными предыдущей записи.

        Если записей больше нет, last_daily_log
        становится null.
        """
        latest_log = (
            DailyLog.objects
            .filter(user=user)
            .order_by("-date", "-created_at")
            .first()
        )

        brain = user.brain

        context = brain.data.setdefault(
            "context",
            {},
        )

        if latest_log:
            context["last_daily_log"] = {
                "date": str(latest_log.date),
                "content": latest_log.content,
            }
        else:
            context["last_daily_log"] = None

        brain.save(
            update_fields=["data"]
        )