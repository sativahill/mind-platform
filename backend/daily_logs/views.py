from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from wins.services import create_daily_log_win

from .ai_service import (
    DailyLogAnalysisError,
    analyze_daily_log,
)
from .models import (
    DailyLog,
    DailyLogSuggestion,
)
from .serializers import (
    DailyLogSerializer,
    DailyLogSuggestionSerializer,
)
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
        log_id = request.query_params.get(
            "id"
        )

        log_date = request.query_params.get(
            "date"
        )

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

    def get_suggestion(
        self,
        request,
        *,
        for_update=False,
    ):
        """
        Находит AI-предложение только внутри
        Daily Logs текущего пользователя.
        """
        suggestion_id = (
            request.query_params.get(
                "suggestion_id"
            )
        )

        if not suggestion_id:
            return None

        queryset = (
            DailyLogSuggestion.objects
            .select_related(
                "daily_log",
                "daily_log__user",
            )
            .filter(
                daily_log__user=(
                    request.user
                )
            )
        )

        if for_update:
            queryset = (
                queryset.select_for_update()
            )

        return get_object_or_404(
            queryset,
            id=suggestion_id,
        )

    def get(self, request):
        action = request.query_params.get(
            "action"
        )

        if action == "suggestions":
            return self.get_suggestions(
                request
            )

        daily_log = self.get_log(
            request
        )

        if daily_log is not None:
            serializer = (
                DailyLogSerializer(
                    daily_log,
                    context={
                        "request": request,
                    },
                )
            )

            return Response(
                serializer.data
            )

        logs = DailyLog.objects.filter(
            user=request.user
        )

        serializer = DailyLogSerializer(
            logs,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data
        )

    def post(self, request):
        action = request.query_params.get(
            "action"
        )

        if action == "analyze":
            return self.analyze(
                request
            )

        if action == "accept":
            return self.accept_suggestion(
                request
            )

        if action == "dismiss":
            return self.dismiss_suggestion(
                request
            )

        if action:
            return Response(
                {
                    "detail": (
                        "Unknown Daily Log action."
                    )
                },
                status=(
                    status
                    .HTTP_400_BAD_REQUEST
                ),
            )

        serializer = DailyLogSerializer(
            data=request.data,
            context={
                "request": request,
            },
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

        response_serializer = (
            DailyLogSerializer(
                daily_log,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            response_serializer.data,
            status=(
                status.HTTP_201_CREATED
            ),
        )

    def patch(self, request):
        daily_log = self.get_log(
            request
        )

        if daily_log is None:
            return Response(
                {
                    "detail": (
                        "Provide the Daily Log "
                        "id or date in the "
                        "query parameters."
                    )
                },
                status=(
                    status
                    .HTTP_400_BAD_REQUEST
                ),
            )

        serializer = DailyLogSerializer(
            daily_log,
            data=request.data,
            partial=True,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        updated_log = serializer.save()

        self.clear_pending_suggestions(
            updated_log
        )

        update_brain_from_daily_log(
            updated_log
        )

        response_serializer = (
            DailyLogSerializer(
                updated_log,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        daily_log = self.get_log(
            request
        )

        if daily_log is None:
            return Response(
                {
                    "detail": (
                        "Provide the Daily Log "
                        "id or date in the "
                        "query parameters."
                    )
                },
                status=(
                    status
                    .HTTP_400_BAD_REQUEST
                ),
            )

        serializer = DailyLogSerializer(
            daily_log,
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        updated_log = serializer.save()

        self.clear_pending_suggestions(
            updated_log
        )

        update_brain_from_daily_log(
            updated_log
        )

        response_serializer = (
            DailyLogSerializer(
                updated_log,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        daily_log = self.get_log(
            request
        )

        if daily_log is None:
            return Response(
                {
                    "detail": (
                        "Provide the Daily Log "
                        "id or date in the "
                        "query parameters."
                    )
                },
                status=(
                    status
                    .HTTP_400_BAD_REQUEST
                ),
            )

        daily_log.delete()

        self.sync_brain_after_delete(
            request.user
        )

        return Response(
            status=(
                status.HTTP_204_NO_CONTENT
            )
        )

    def analyze(self, request):
        """
        Запускает Gemini-анализ одной записи.

        POST:
        /api/daily-logs/?id=12&action=analyze
        """
        daily_log = self.get_log(
            request
        )

        if daily_log is None:
            return Response(
                {
                    "detail": (
                        "Provide the Daily Log "
                        "id or date before "
                        "starting analysis."
                    )
                },
                status=(
                    status
                    .HTTP_400_BAD_REQUEST
                ),
            )

        try:
            suggestions = analyze_daily_log(
                daily_log
            )
        except DailyLogAnalysisError as error:
            return Response(
                {
                    "detail": str(error),
                    "daily_log_saved": True,
                },
                status=(
                    status
                    .HTTP_503_SERVICE_UNAVAILABLE
                ),
            )

        serializer = (
            DailyLogSuggestionSerializer(
                suggestions,
                many=True,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            {
                "daily_log": daily_log.id,
                "suggestions": (
                    serializer.data
                ),
                "suggestions_count": len(
                    suggestions
                ),
            },
            status=status.HTTP_200_OK,
        )

    def get_suggestions(self, request):
        """
        Возвращает предложения конкретного лога.

        По умолчанию возвращает только pending.

        GET:
        /api/daily-logs/
        ?id=12
        &action=suggestions

        Можно явно указать:

        &status=accepted
        &status=dismissed
        &status=all
        """
        daily_log = self.get_log(
            request
        )

        if daily_log is None:
            return Response(
                {
                    "detail": (
                        "Provide the Daily Log "
                        "id or date to retrieve "
                        "suggestions."
                    )
                },
                status=(
                    status
                    .HTTP_400_BAD_REQUEST
                ),
            )

        requested_status = (
            request.query_params.get(
                "status",
                DailyLogSuggestion
                .STATUS_PENDING,
            )
        )

        suggestions = (
            DailyLogSuggestion.objects
            .filter(
                daily_log=daily_log
            )
            .order_by("created_at")
        )

        if requested_status != "all":
            valid_statuses = {
                choice[0]
                for choice
                in (
                    DailyLogSuggestion
                    .STATUS_CHOICES
                )
            }

            if (
                requested_status
                not in valid_statuses
            ):
                return Response(
                    {
                        "detail": (
                            "Invalid suggestion "
                            "status."
                        )
                    },
                    status=(
                        status
                        .HTTP_400_BAD_REQUEST
                    ),
                )

            suggestions = (
                suggestions.filter(
                    status=requested_status
                )
            )

        serializer = (
            DailyLogSuggestionSerializer(
                suggestions,
                many=True,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def accept_suggestion(
        self,
        request,
    ):
        """
        Подтверждает AI-предложение и создаёт Win.

        POST:
        /api/daily-logs/
        ?suggestion_id=7
        &action=accept
        """
        with transaction.atomic():
            suggestion = (
                self.get_suggestion(
                    request,
                    for_update=True,
                )
            )

            if suggestion is None:
                return Response(
                    {
                        "detail": (
                            "Provide a "
                            "suggestion_id."
                        )
                    },
                    status=(
                        status
                        .HTTP_400_BAD_REQUEST
                    ),
                )

            if (
                suggestion.suggestion_type
                != DailyLogSuggestion.TYPE_WIN
            ):
                return Response(
                    {
                        "detail": (
                            "This suggestion type "
                            "cannot be accepted yet."
                        )
                    },
                    status=(
                        status
                        .HTTP_400_BAD_REQUEST
                    ),
                )

            if (
                suggestion.status
                == DailyLogSuggestion
                .STATUS_DISMISSED
            ):
                return Response(
                    {
                        "detail": (
                            "A dismissed suggestion "
                            "cannot be accepted."
                        )
                    },
                    status=(
                        status.HTTP_409_CONFLICT
                    ),
                )

            win, created = (
                create_daily_log_win(
                    daily_log=(
                        suggestion.daily_log
                    ),
                    title=(
                        suggestion.title
                    ),
                    description=(
                        suggestion.description
                    ),
                    size=suggestion.size,
                    suggestion_key=(
                        suggestion
                        .suggestion_key
                    ),
                    suggestion_id=str(
                        suggestion.id
                    ),
                )
            )

            if (
                suggestion.status
                != DailyLogSuggestion
                .STATUS_ACCEPTED
            ):
                suggestion.status = (
                    DailyLogSuggestion
                    .STATUS_ACCEPTED
                )

                suggestion.resolved_at = (
                    timezone.now()
                )

                suggestion.save(
                    update_fields=[
                        "status",
                        "resolved_at",
                        "updated_at",
                    ]
                )

        return Response(
            {
                "suggestion": (
                    DailyLogSuggestionSerializer(
                        suggestion,
                        context={
                            "request": request,
                        },
                    ).data
                ),
                "win": {
                    "id": win.id,
                    "title": win.title,
                    "description": (
                        win.description
                    ),
                    "date": str(win.date),
                    "size": win.size,
                    "source": win.source,
                    "source_id": (
                        win.source_id
                    ),
                },
                "win_created": created,
            },
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )

    def dismiss_suggestion(
        self,
        request,
    ):
        """
        Отклоняет AI-предложение.

        POST:
        /api/daily-logs/
        ?suggestion_id=7
        &action=dismiss
        """
        with transaction.atomic():
            suggestion = (
                self.get_suggestion(
                    request,
                    for_update=True,
                )
            )

            if suggestion is None:
                return Response(
                    {
                        "detail": (
                            "Provide a "
                            "suggestion_id."
                        )
                    },
                    status=(
                        status
                        .HTTP_400_BAD_REQUEST
                    ),
                )

            if (
                suggestion.status
                == DailyLogSuggestion
                .STATUS_ACCEPTED
            ):
                return Response(
                    {
                        "detail": (
                            "An accepted suggestion "
                            "cannot be dismissed."
                        )
                    },
                    status=(
                        status.HTTP_409_CONFLICT
                    ),
                )

            if (
                suggestion.status
                != DailyLogSuggestion
                .STATUS_DISMISSED
            ):
                suggestion.status = (
                    DailyLogSuggestion
                    .STATUS_DISMISSED
                )

                suggestion.resolved_at = (
                    timezone.now()
                )

                suggestion.save(
                    update_fields=[
                        "status",
                        "resolved_at",
                        "updated_at",
                    ]
                )

        serializer = (
            DailyLogSuggestionSerializer(
                suggestion,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def clear_pending_suggestions(
        daily_log,
    ):
        """
        После изменения текста старые pending-предложения
        больше не соответствуют записи и удаляются.

        Accepted и dismissed сохраняются как история
        решений пользователя.
        """
        daily_log.suggestions.filter(
            status=(
                DailyLogSuggestion
                .STATUS_PENDING
            )
        ).delete()

    @staticmethod
    def sync_brain_after_delete(user):
        """
        После удаления текущего последнего лога
        обновляет Brain данными предыдущей записи.

        Если записей больше нет,
        last_daily_log становится null.
        """
        latest_log = (
            DailyLog.objects
            .filter(user=user)
            .order_by(
                "-date",
                "-created_at",
            )
            .first()
        )

        brain = user.brain
        brain_data = brain.data or {}

        context = brain_data.setdefault(
            "context",
            {},
        )

        if latest_log:
            context[
                "last_daily_log"
            ] = {
                "date": str(
                    latest_log.date
                ),
                "content": (
                    latest_log.content
                ),
            }
        else:
            context[
                "last_daily_log"
            ] = None

        brain.data = brain_data

        brain.save(
            update_fields=["data"]
        )
