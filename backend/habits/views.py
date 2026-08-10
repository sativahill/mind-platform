from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Habit, HabitCompletion
from .serializers import HabitSerializer


def get_user_habit(
    request,
    habit_id,
):
    return get_object_or_404(
        Habit,
        id=habit_id,
        user=request.user,
    )


class HabitView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        habits = (
            Habit.objects
            .filter(
                user=request.user
            )
            .prefetch_related(
                "completions"
            )
        )

        status_filter = (
            request.query_params.get(
                "status"
            )
        )

        if status_filter in {
            Habit.Status.ACTIVE,
            Habit.Status.ARCHIVED,
        }:
            habits = habits.filter(
                status=status_filter
            )

        serializer = HabitSerializer(
            habits,
            many=True,
        )

        return Response(
            serializer.data
        )

    def post(self, request):
        serializer = HabitSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        habit = Habit.objects.create(
            user=request.user,
            title=serializer.validated_data[
                "title"
            ],
            trigger=serializer.validated_data[
                "trigger"
            ],
            action=serializer.validated_data[
                "action"
            ],
            reward=serializer.validated_data.get(
                "reward",
                "",
            ),
            status=Habit.Status.ACTIVE,
        )

        return Response(
            HabitSerializer(
                habit
            ).data,
            status=201,
        )


class HabitDetailView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        habit_id,
    ):
        habit = get_user_habit(
            request,
            habit_id,
        )

        return Response(
            HabitSerializer(
                habit
            ).data
        )

    def patch(
        self,
        request,
        habit_id,
    ):
        habit = get_user_habit(
            request,
            habit_id,
        )

        serializer = HabitSerializer(
            habit,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        updated_habit = (
            serializer.save()
        )

        return Response(
            HabitSerializer(
                updated_habit
            ).data
        )

    def delete(
        self,
        request,
        habit_id,
    ):
        habit = get_user_habit(
            request,
            habit_id,
        )

        habit.delete()

        return Response(
            status=204
        )


class HabitCompleteView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    @transaction.atomic
    def post(
        self,
        request,
        habit_id,
    ):
        habit = get_user_habit(
            request,
            habit_id,
        )

        if (
            habit.status
            == Habit.Status.ARCHIVED
        ):
            return Response(
                {
                    "detail": (
                        "Archived habits "
                        "cannot be completed."
                    )
                },
                status=400,
            )

        today = (
            timezone.localdate()
        )

        HabitCompletion.objects.update_or_create(
            habit=habit,
            completed_at=today,
            defaults={
                "status": (
                    HabitCompletion
                    .Status
                    .COMPLETED
                )
            },
        )

        habit.refresh_streak()

        return Response(
            HabitSerializer(
                habit
            ).data
        )


class HabitMissView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    @transaction.atomic
    def post(
        self,
        request,
        habit_id,
    ):
        habit = get_user_habit(
            request,
            habit_id,
        )

        if (
            habit.status
            == Habit.Status.ARCHIVED
        ):
            return Response(
                {
                    "detail": (
                        "Archived habits "
                        "cannot be marked "
                        "as missed."
                    )
                },
                status=400,
            )

        today = (
            timezone.localdate()
        )

        HabitCompletion.objects.update_or_create(
            habit=habit,
            completed_at=today,
            defaults={
                "status": (
                    HabitCompletion
                    .Status
                    .MISSED
                )
            },
        )

        habit.refresh_streak()

        return Response(
            HabitSerializer(
                habit
            ).data
        )


class HabitArchiveView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        habit_id,
    ):
        habit = get_user_habit(
            request,
            habit_id,
        )

        if (
            habit.status
            != Habit.Status.ARCHIVED
        ):
            habit.status = (
                Habit.Status.ARCHIVED
            )

            habit.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        return Response(
            HabitSerializer(
                habit
            ).data
        )


class HabitRestoreView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        habit_id,
    ):
        habit = get_user_habit(
            request,
            habit_id,
        )

        if (
            habit.status
            != Habit.Status.ACTIVE
        ):
            habit.status = (
                Habit.Status.ACTIVE
            )

            habit.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        habit.refresh_streak()

        return Response(
            HabitSerializer(
                habit
            ).data
        )