from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from daily_logs.models import DailyLog
from goals.models import Goal
from habits.models import Habit, HabitCompletion
from wins.models import Win


class HomeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.localdate()

        brain = user.brain

        daily_logs = DailyLog.objects.filter(
            user=user
        )

        wins = Win.objects.filter(
            user=user
        )

        active_goals = Goal.objects.filter(
            user=user,
            status=Goal.ACTIVE,
        )

        habits = Habit.objects.filter(
            user=user
        )

        last_daily_log = daily_logs.order_by(
            "-date"
        ).first()

        last_win = wins.order_by(
            "-id"
        ).first()

        primary_goal = active_goals.order_by(
            "-updated_at"
        ).first()

        latest_habit = habits.order_by(
            "-updated_at"
        ).first()

        habits_completed_today = (
            HabitCompletion.objects.filter(
                habit__user=user,
                completed_at=today,
            )
            .values("habit_id")
            .distinct()
            .count()
        )

        highest_streak = (
            habits.order_by("-streak")
            .values_list("streak", flat=True)
            .first()
            or 0
        )

        return Response(
            {
                "brain": brain.data,
                "daily_logs_count": daily_logs.count(),
                "wins_count": wins.count(),

                "last_daily_log": (
                    {
                        "date": str(last_daily_log.date),
                        "content": last_daily_log.content,
                    }
                    if last_daily_log
                    else None
                ),

                "last_win": (
                    {
                        "title": last_win.title,
                        "size": last_win.size,
                    }
                    if last_win
                    else None
                ),

                "goals": {
                    "active_count": active_goals.count(),
                    "primary": (
                        {
                            "id": primary_goal.id,
                            "title": primary_goal.title,
                            "progress": primary_goal.progress,
                        }
                        if primary_goal
                        else None
                    ),
                },

                "habits": {
                    "active_count": habits.count(),
                    "completed_today": habits_completed_today,
                    "highest_streak": highest_streak,
                    "latest": (
                        {
                            "id": latest_habit.id,
                            "title": latest_habit.title,
                            "streak": latest_habit.streak,
                        }
                        if latest_habit
                        else None
                    ),
                },
            }
        )