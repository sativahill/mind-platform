from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIClient

from habits.models import Habit, HabitCompletion


User = get_user_model()


class HomeHabitAggregationTests(TestCase):
    HOME_URL = "/api/home/"

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="home-habits-user",
            email="home-habits@example.com",
            password="test-password-123",
        )

        self.client.force_authenticate(
            user=self.user
        )

    def create_habit(
        self,
        *,
        title,
        habit_status=Habit.Status.ACTIVE,
        streak=0,
    ):
        return Habit.objects.create(
            user=self.user,
            title=title,
            trigger="After breakfast",
            action="Read one page",
            reward="Coffee",
            status=habit_status,
            streak=streak,
        )

    def test_archived_habit_is_excluded_from_active_count(
        self,
    ):
        self.create_habit(
            title="Active habit"
        )

        self.create_habit(
            title="Archived habit",
            habit_status=Habit.Status.ARCHIVED,
        )

        response = self.client.get(
            self.HOME_URL
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["habits"]["active_count"],
            1,
        )

    def test_missed_habit_is_not_completed_today(self):
        habit = self.create_habit(
            title="Missed habit"
        )

        HabitCompletion.objects.create(
            habit=habit,
            completed_at=timezone.localdate(),
            status=HabitCompletion.Status.MISSED,
        )

        response = self.client.get(
            self.HOME_URL
        )

        self.assertEqual(
            response.data["habits"]["completed_today"],
            0,
        )

    def test_completed_habit_is_counted_today(self):
        habit = self.create_habit(
            title="Completed habit"
        )

        HabitCompletion.objects.create(
            habit=habit,
            completed_at=timezone.localdate(),
            status=(
                HabitCompletion.Status.COMPLETED
            ),
        )

        response = self.client.get(
            self.HOME_URL
        )

        self.assertEqual(
            response.data["habits"]["completed_today"],
            1,
        )

    def test_latest_habit_excludes_archived_habit(self):
        active_habit = self.create_habit(
            title="Active habit"
        )

        archived_habit = self.create_habit(
            title="Newest archived habit",
            habit_status=Habit.Status.ARCHIVED,
        )

        Habit.objects.filter(
            id=archived_habit.id
        ).update(
            updated_at=(
                timezone.now()
                + timedelta(hours=1)
            )
        )

        response = self.client.get(
            self.HOME_URL
        )

        self.assertEqual(
            response.data["habits"]["latest"]["id"],
            active_habit.id,
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_highest_streak_is_refreshed_from_completions(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit(
            title="Current streak",
            streak=99,
        )

        created_at = timezone.make_aware(
            datetime.combine(
                date(2026, 8, 8),
                time.min,
            )
        )

        Habit.objects.filter(
            id=habit.id
        ).update(
            created_at=created_at
        )

        for completion_date in (
            date(2026, 8, 8),
            date(2026, 8, 9),
        ):
            HabitCompletion.objects.create(
                habit=habit,
                completed_at=completion_date,
                status=(
                    HabitCompletion
                    .Status
                    .COMPLETED
                ),
            )

        response = self.client.get(
            self.HOME_URL
        )

        self.assertEqual(
            response.data["habits"]["highest_streak"],
            2,
        )

        self.assertEqual(
            response.data["habits"]["latest"]["streak"],
            2,
        )

        habit.refresh_from_db()

        self.assertEqual(
            habit.streak,
            2,
        )
