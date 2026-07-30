from secrets import randbelow

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

    @staticmethod
    def get_random_win(wins, today):
        """
        Выбирает случайную победу из прошлого.

        Сначала пытаемся взять победу, произошедшую раньше
        сегодняшнего дня. Если таких ещё нет, используем любую
        существующую победу.

        Не используем order_by("?"), чтобы база не сортировала
        случайным образом весь queryset.
        """
        historical_wins = wins.filter(
            date__lt=today
        )

        source_queryset = (
            historical_wins
            if historical_wins.exists()
            else wins
        )

        wins_count = source_queryset.count()

        if wins_count == 0:
            return None

        random_offset = randbelow(
            wins_count
        )

        return source_queryset[
            random_offset
        ]

    def get(self, request):
        user = request.user
        today = timezone.localdate()

        brain = user.brain

        daily_logs = DailyLog.objects.filter(
            user=user
        )

        wins = Win.objects.filter(
            user=user
        ).order_by(
            "-date",
            "-created_at",
        )

        active_goals = Goal.objects.filter(
            user=user,
            status=Goal.ACTIVE,
        )

        habits = Habit.objects.filter(
            user=user
        )

        last_daily_log = (
            daily_logs
            .order_by(
                "-date",
                "-created_at",
            )
            .first()
        )

        last_win = wins.first()

        random_win = self.get_random_win(
            wins=wins,
            today=today,
        )

        primary_goal = (
            active_goals
            .order_by("-updated_at")
            .first()
        )

        latest_habit = (
            habits
            .order_by("-updated_at")
            .first()
        )

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
            habits
            .order_by("-streak")
            .values_list(
                "streak",
                flat=True,
            )
            .first()
            or 0
        )

        return Response(
            {
                "brain": brain.data,

                "daily_logs_count": (
                    daily_logs.count()
                ),

                "wins_count": wins.count(),

                "last_daily_log": (
                    {
                        "id": last_daily_log.id,
                        "date": str(
                            last_daily_log.date
                        ),
                        "content": (
                            last_daily_log.content
                        ),
                    }
                    if last_daily_log
                    else None
                ),

                # Временно оставляем для совместимости
                # с текущим Home frontend.
                "last_win": (
                    {
                        "id": last_win.id,
                        "title": last_win.title,
                        "description": (
                            last_win.description
                        ),
                        "date": str(
                            last_win.date
                        ),
                        "size": last_win.size,
                        "source": last_win.source,
                    }
                    if last_win
                    else None
                ),

                # Основная механика из ТЗ:
                # случайная победа из прошлого.
                "random_win": (
                    {
                        "id": random_win.id,
                        "title": random_win.title,
                        "description": (
                            random_win.description
                        ),
                        "date": str(
                            random_win.date
                        ),
                        "size": random_win.size,
                        "source": random_win.source,
                    }
                    if random_win
                    else None
                ),

                "goals": {
                    "active_count": (
                        active_goals.count()
                    ),

                    "primary": (
                        {
                            "id": primary_goal.id,
                            "title": (
                                primary_goal.title
                            ),
                            "progress": (
                                primary_goal.progress
                            ),
                        }
                        if primary_goal
                        else None
                    ),
                },

                "habits": {
                    "active_count": (
                        habits.count()
                    ),

                    "completed_today": (
                        habits_completed_today
                    ),

                    "highest_streak": (
                        highest_streak
                    ),

                    "latest": (
                        {
                            "id": latest_habit.id,
                            "title": (
                                latest_habit.title
                            ),
                            "streak": (
                                latest_habit.streak
                            ),
                        }
                        if latest_habit
                        else None
                    ),
                },
            }
        )