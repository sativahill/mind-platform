from datetime import date

from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Habit, HabitCompletion
from .serializers import HabitSerializer


class HabitView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        habits = Habit.objects.filter(
            user=request.user
        )

        serializer = HabitSerializer(
            habits,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = HabitSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        habit = Habit.objects.create(
            user=request.user,
            title=serializer.validated_data["title"],
            trigger=serializer.validated_data["trigger"],
            action=serializer.validated_data["action"],
            reward=serializer.validated_data.get(
                "reward",
                "",
            ),
        )

        return Response(
            HabitSerializer(habit).data,
            status=201,
        )


class HabitCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, habit_id):
        habit = get_object_or_404(
            Habit,
            id=habit_id,
            user=request.user,
        )

        today = date.today()

        already_completed = (
            HabitCompletion.objects.filter(
                habit=habit,
                completed_at=today,
            ).exists()
        )

        if not already_completed:
            HabitCompletion.objects.create(
                habit=habit,
                completed_at=today,
            )

        habit.streak = (
            HabitCompletion.objects.filter(
                habit=habit
            ).count()
        )

        habit.save()

        return Response(
            HabitSerializer(habit).data
        )