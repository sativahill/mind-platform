from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from wins.models import Win

from .models import Habit, HabitCompletion


User = get_user_model()


class HabitAPITestCase(APITestCase):
    HABITS_URL = "/api/habits/"

    def setUp(self):
        self.user = User.objects.create_user(
            username="habit-user",
            email="habit-user@test.com",
            password="test-password-123",
        )

        self.other_user = User.objects.create_user(
            username="other-habit-user",
            email="other-habit-user@test.com",
            password="test-password-123",
        )

        self.client.force_authenticate(
            user=self.user
        )

    def habit_detail_url(
        self,
        habit_id,
    ):
        return (
            f"/api/habits/{habit_id}/"
        )

    def habit_complete_url(
        self,
        habit_id,
    ):
        return (
            f"/api/habits/"
            f"{habit_id}/complete/"
        )

    def habit_miss_url(
        self,
        habit_id,
    ):
        return (
            f"/api/habits/"
            f"{habit_id}/miss/"
        )

    def habit_archive_url(
        self,
        habit_id,
    ):
        return (
            f"/api/habits/"
            f"{habit_id}/archive/"
        )

    def habit_restore_url(
        self,
        habit_id,
    ):
        return (
            f"/api/habits/"
            f"{habit_id}/restore/"
        )

    def create_habit(
        self,
        *,
        user=None,
        title="Read every day",
        trigger="After breakfast",
        action="Read one page",
        reward="Make coffee",
        status_value=Habit.Status.ACTIVE,
    ):
        habit = Habit.objects.create(
            user=user or self.user,
            title=title,
            trigger=trigger,
            action=action,
            reward=reward,
            status=status_value,
        )

        self.set_habit_created_date(
            habit,
            timezone.localdate(),
        )

        return habit

    def set_habit_created_date(
        self,
        habit,
        created_date,
    ):
        created_at = timezone.make_aware(
            datetime.combine(
                created_date,
                time.min,
            )
        )

        Habit.objects.filter(
            pk=habit.pk
        ).update(
            created_at=created_at
        )

        habit.created_at = created_at

    def create_completion(
        self,
        habit,
        completion_date,
        completion_status=(
            HabitCompletion.Status.COMPLETED
        ),
    ):
        if habit.created_at.date() > completion_date:
            self.set_habit_created_date(
                habit,
                completion_date,
            )

        return HabitCompletion.objects.create(
            habit=habit,
            completed_at=completion_date,
            status=completion_status,
        )

    def create_habit_via_api(
        self,
        *,
        title="Read every day",
    ):
        response = self.client.post(
            self.HABITS_URL,
            {
                "title": title,
                "trigger": "After breakfast",
                "action": "Read one page",
                "reward": "Make coffee",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        return Habit.objects.get(
            id=response.data["id"]
        )

    def get_brain_habits(self):
        self.user.brain.refresh_from_db()

        return self.user.brain.data[
            "habits"
        ]

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_authentication_is_required(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.get(
            self.HABITS_URL
        )

        self.assertIn(
            response.status_code,
            (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ),
        )

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    def test_create_habit(self):
        payload = {
            "title": "Learn English",
            "trigger": "After breakfast",
            "action": "Review 5 words",
            "reward": "Drink coffee",
        }

        response = self.client.post(
            self.HABITS_URL,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Habit.objects.filter(
                user=self.user
            ).count(),
            1,
        )

        habit = Habit.objects.get(
            user=self.user
        )

        self.assertEqual(
            habit.title,
            "Learn English",
        )

        self.assertEqual(
            habit.trigger,
            "After breakfast",
        )

        self.assertEqual(
            habit.action,
            "Review 5 words",
        )

        self.assertEqual(
            habit.reward,
            "Drink coffee",
        )

        self.assertEqual(
            habit.status,
            Habit.Status.ACTIVE,
        )

        self.assertEqual(
            habit.streak,
            0,
        )

        self.assertEqual(
            response.data["today_status"],
            "pending",
        )

        self.assertFalse(
            response.data["completed_today"]
        )

    def test_create_habit_reward_is_optional(self):
        payload = {
            "title": "Read",
            "trigger": "Before bed",
            "action": "Read one page",
        }

        response = self.client.post(
            self.HABITS_URL,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        habit = Habit.objects.get(
            user=self.user
        )

        self.assertEqual(
            habit.reward,
            "",
        )

    def test_create_habit_strips_whitespace(self):
        payload = {
            "title": "  Read every day  ",
            "trigger": "  After breakfast  ",
            "action": "  Read one page  ",
            "reward": "  Coffee  ",
        }

        response = self.client.post(
            self.HABITS_URL,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        habit = Habit.objects.get(
            user=self.user
        )

        self.assertEqual(
            habit.title,
            "Read every day",
        )

        self.assertEqual(
            habit.trigger,
            "After breakfast",
        )

        self.assertEqual(
            habit.action,
            "Read one page",
        )

        self.assertEqual(
            habit.reward,
            "Coffee",
        )

    def test_create_habit_rejects_empty_title(self):
        payload = {
            "title": "   ",
            "trigger": "After breakfast",
            "action": "Read one page",
            "reward": "",
        }

        response = self.client.post(
            self.HABITS_URL,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_create_habit_rejects_empty_trigger(self):
        payload = {
            "title": "Read",
            "trigger": "   ",
            "action": "Read one page",
            "reward": "",
        }

        response = self.client.post(
            self.HABITS_URL,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_create_habit_rejects_empty_action(self):
        payload = {
            "title": "Read",
            "trigger": "After breakfast",
            "action": "   ",
            "reward": "",
        }

        response = self.client.post(
            self.HABITS_URL,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # ---------------------------------------------------------
    # List
    # ---------------------------------------------------------

    def test_list_returns_only_current_user_habits(self):
        own_habit = self.create_habit(
            title="Own habit"
        )

        self.create_habit(
            user=self.other_user,
            title="Other habit",
        )

        response = self.client.get(
            self.HABITS_URL
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            habit["id"]
            for habit in response.data
        }

        self.assertEqual(
            returned_ids,
            {own_habit.id},
        )

    def test_list_can_filter_active_habits(self):
        active = self.create_habit(
            title="Active"
        )

        self.create_habit(
            title="Archived",
            status_value=(
                Habit.Status.ARCHIVED
            ),
        )

        response = self.client.get(
            self.HABITS_URL,
            {
                "status": "active",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["id"],
            active.id,
        )

    def test_list_can_filter_archived_habits(self):
        self.create_habit(
            title="Active"
        )

        archived = self.create_habit(
            title="Archived",
            status_value=(
                Habit.Status.ARCHIVED
            ),
        )

        response = self.client.get(
            self.HABITS_URL,
            {
                "status": "archived",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["id"],
            archived.id,
        )

    # ---------------------------------------------------------
    # Detail
    # ---------------------------------------------------------

    def test_get_habit_detail(self):
        habit = self.create_habit()

        response = self.client.get(
            self.habit_detail_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            habit.id,
        )

        self.assertEqual(
            response.data["title"],
            habit.title,
        )

    def test_cannot_get_other_users_habit(self):
        habit = self.create_habit(
            user=self.other_user
        )

        response = self.client.get(
            self.habit_detail_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # ---------------------------------------------------------
    # Update
    # ---------------------------------------------------------

    def test_patch_habit(self):
        habit = self.create_habit()

        response = self.client.patch(
            self.habit_detail_url(
                habit.id
            ),
            {
                "title": "Updated habit",
                "trigger": "After lunch",
                "action": "Read two pages",
                "reward": "Tea",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        habit.refresh_from_db()

        self.assertEqual(
            habit.title,
            "Updated habit",
        )

        self.assertEqual(
            habit.trigger,
            "After lunch",
        )

        self.assertEqual(
            habit.action,
            "Read two pages",
        )

        self.assertEqual(
            habit.reward,
            "Tea",
        )

    def test_cannot_patch_other_users_habit(self):
        habit = self.create_habit(
            user=self.other_user
        )

        response = self.client.patch(
            self.habit_detail_url(
                habit.id
            ),
            {
                "title": "Hacked",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        habit.refresh_from_db()

        self.assertNotEqual(
            habit.title,
            "Hacked",
        )

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------

    def test_delete_habit(self):
        habit = self.create_habit()

        response = self.client.delete(
            self.habit_detail_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Habit.objects.filter(
                id=habit.id
            ).exists()
        )

    def test_delete_habit_deletes_completions(self):
        habit = self.create_habit()

        self.create_completion(
            habit,
            date(2026, 8, 10),
        )

        self.client.delete(
            self.habit_detail_url(
                habit.id
            )
        )

        self.assertFalse(
            HabitCompletion.objects.filter(
                habit_id=habit.id
            ).exists()
        )

    def test_cannot_delete_other_users_habit(self):
        habit = self.create_habit(
            user=self.other_user
        )

        response = self.client.delete(
            self.habit_detail_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertTrue(
            Habit.objects.filter(
                id=habit.id
            ).exists()
        )

    # ---------------------------------------------------------
    # Complete today
    # ---------------------------------------------------------

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_complete_habit_today(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        response = self.client.post(
            self.habit_complete_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        completion = (
            HabitCompletion.objects.get(
                habit=habit,
                completed_at=date(
                    2026,
                    8,
                    10,
                ),
            )
        )

        self.assertEqual(
            completion.status,
            HabitCompletion.Status.COMPLETED,
        )

        self.assertTrue(
            response.data["completed_today"]
        )

        self.assertEqual(
            response.data["today_status"],
            "completed",
        )

        self.assertEqual(
            response.data["streak"],
            1,
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_double_complete_does_not_duplicate_day(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        self.client.post(
            self.habit_complete_url(
                habit.id
            )
        )

        self.client.post(
            self.habit_complete_url(
                habit.id
            )
        )

        self.assertEqual(
            HabitCompletion.objects.filter(
                habit=habit,
                completed_at=date(
                    2026,
                    8,
                    10,
                ),
            ).count(),
            1,
        )

    def test_cannot_complete_other_users_habit(self):
        habit = self.create_habit(
            user=self.other_user
        )

        response = self.client.post(
            self.habit_complete_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # ---------------------------------------------------------
    # Miss today
    # ---------------------------------------------------------

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_mark_habit_missed_today(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        response = self.client.post(
            self.habit_miss_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        completion = (
            HabitCompletion.objects.get(
                habit=habit,
                completed_at=date(
                    2026,
                    8,
                    10,
                ),
            )
        )

        self.assertEqual(
            completion.status,
            HabitCompletion.Status.MISSED,
        )

        self.assertFalse(
            response.data["completed_today"]
        )

        self.assertEqual(
            response.data["today_status"],
            "missed",
        )

        self.assertEqual(
            response.data["streak"],
            0,
        )

    # ---------------------------------------------------------
    # Correcting today's state
    # ---------------------------------------------------------

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_missed_can_be_changed_to_completed(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        self.client.post(
            self.habit_miss_url(
                habit.id
            )
        )

        response = self.client.post(
            self.habit_complete_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        completion = (
            HabitCompletion.objects.get(
                habit=habit,
                completed_at=date(
                    2026,
                    8,
                    10,
                ),
            )
        )

        self.assertEqual(
            completion.status,
            HabitCompletion.Status.COMPLETED,
        )

        self.assertEqual(
            HabitCompletion.objects.filter(
                habit=habit,
                completed_at=date(
                    2026,
                    8,
                    10,
                ),
            ).count(),
            1,
        )

        self.assertEqual(
            response.data["today_status"],
            "completed",
        )

        self.assertEqual(
            response.data["streak"],
            1,
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_completed_can_be_changed_to_missed(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        self.client.post(
            self.habit_complete_url(
                habit.id
            )
        )

        response = self.client.post(
            self.habit_miss_url(
                habit.id
            )
        )

        completion = (
            HabitCompletion.objects.get(
                habit=habit,
                completed_at=date(
                    2026,
                    8,
                    10,
                ),
            )
        )

        self.assertEqual(
            completion.status,
            HabitCompletion.Status.MISSED,
        )

        self.assertEqual(
            response.data["today_status"],
            "missed",
        )

        self.assertEqual(
            response.data["streak"],
            0,
        )

    # ---------------------------------------------------------
    # Real streak
    # ---------------------------------------------------------

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_streak_counts_consecutive_completed_days(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        self.create_completion(
            habit,
            date(2026, 8, 8),
        )

        self.create_completion(
            habit,
            date(2026, 8, 9),
        )

        self.create_completion(
            habit,
            date(2026, 8, 10),
        )

        streak = (
            habit.calculate_streak()
        )

        self.assertEqual(
            streak,
            3,
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_missed_today_breaks_streak(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        self.create_completion(
            habit,
            date(2026, 8, 8),
        )

        self.create_completion(
            habit,
            date(2026, 8, 9),
        )

        self.create_completion(
            habit,
            date(2026, 8, 10),
            HabitCompletion.Status.MISSED,
        )

        self.assertEqual(
            habit.calculate_streak(),
            0,
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_previous_miss_breaks_old_streak(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        self.create_completion(
            habit,
            date(2026, 8, 6),
        )

        self.create_completion(
            habit,
            date(2026, 8, 7),
        )

        self.create_completion(
            habit,
            date(2026, 8, 8),
            HabitCompletion.Status.MISSED,
        )

        self.create_completion(
            habit,
            date(2026, 8, 9),
        )

        self.create_completion(
            habit,
            date(2026, 8, 10),
        )

        self.assertEqual(
            habit.calculate_streak(),
            2,
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_pending_today_preserves_yesterday_streak(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        self.create_completion(
            habit,
            date(2026, 8, 8),
        )

        self.create_completion(
            habit,
            date(2026, 8, 9),
        )

        self.assertEqual(
            habit.calculate_streak(),
            2,
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_gap_breaks_streak(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        self.create_completion(
            habit,
            date(2026, 8, 7),
        )

        # August 8 has no record.

        self.create_completion(
            habit,
            date(2026, 8, 9),
        )

        self.create_completion(
            habit,
            date(2026, 8, 10),
        )

        self.assertEqual(
            habit.calculate_streak(),
            2,
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 11),
    )
    def test_past_missing_day_breaks_streak(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        self.create_completion(
            habit,
            date(2026, 8, 8),
        )

        self.create_completion(
            habit,
            date(2026, 8, 9),
        )

        self.assertEqual(
            habit.calculate_streak(),
            0,
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 11),
    )
    def test_pending_today_preserves_previous_streak(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        self.create_completion(
            habit,
            date(2026, 8, 9),
        )

        self.create_completion(
            habit,
            date(2026, 8, 10),
        )

        self.assertEqual(
            habit.calculate_streak(),
            2,
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_complete_endpoint_refreshes_persisted_streak(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        self.create_completion(
            habit,
            date(2026, 8, 8),
        )

        self.create_completion(
            habit,
            date(2026, 8, 9),
        )

        response = self.client.post(
            self.habit_complete_url(
                habit.id
            )
        )

        habit.refresh_from_db()

        self.assertEqual(
            habit.streak,
            3,
        )

        self.assertEqual(
            response.data["streak"],
            3,
        )

    # ---------------------------------------------------------
    # Consecutive misses
    # ---------------------------------------------------------

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_consecutive_misses_are_counted(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        for day in (
            date(2026, 8, 8),
            date(2026, 8, 9),
            date(2026, 8, 10),
        ):
            self.create_completion(
                habit,
                day,
                HabitCompletion.Status.MISSED,
            )

        self.assertEqual(
            habit.consecutive_misses(),
            3,
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_pending_today_preserves_miss_chain(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        self.create_completion(
            habit,
            date(2026, 8, 8),
            HabitCompletion.Status.MISSED,
        )

        self.create_completion(
            habit,
            date(2026, 8, 9),
            HabitCompletion.Status.MISSED,
        )

        self.assertEqual(
            habit.consecutive_misses(),
            2,
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_completion_resets_consecutive_misses(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        self.create_completion(
            habit,
            date(2026, 8, 8),
            HabitCompletion.Status.MISSED,
        )

        self.create_completion(
            habit,
            date(2026, 8, 9),
            HabitCompletion.Status.MISSED,
        )

        self.create_completion(
            habit,
            date(2026, 8, 10),
            HabitCompletion.Status.COMPLETED,
        )

        self.assertEqual(
            habit.consecutive_misses(),
            0,
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 11),
    )
    def test_missing_past_days_count_as_consecutive_misses(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        self.create_completion(
            habit,
            date(2026, 8, 8),
        )

        self.assertEqual(
            habit.consecutive_misses(),
            2,
        )

    # ---------------------------------------------------------
    # Recent days
    # ---------------------------------------------------------

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_recent_days_returns_seven_days(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        response = self.client.get(
            self.habit_detail_url(
                habit.id
            )
        )

        recent_days = (
            response.data["recent_days"]
        )

        self.assertEqual(
            len(recent_days),
            7,
        )

        self.assertEqual(
            recent_days[0]["date"],
            "2026-08-04",
        )

        self.assertEqual(
            recent_days[-1]["date"],
            "2026-08-10",
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_recent_days_contains_day_statuses(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        self.create_completion(
            habit,
            date(2026, 8, 8),
            HabitCompletion.Status.COMPLETED,
        )

        self.create_completion(
            habit,
            date(2026, 8, 9),
            HabitCompletion.Status.MISSED,
        )

        response = self.client.get(
            self.habit_detail_url(
                habit.id
            )
        )

        statuses = {
            item["date"]:
                item["status"]
            for item in (
                response.data[
                    "recent_days"
                ]
            )
        }

        self.assertEqual(
            statuses["2026-08-08"],
            "completed",
        )

        self.assertEqual(
            statuses["2026-08-09"],
            "missed",
        )

        self.assertEqual(
            statuses["2026-08-10"],
            "pending",
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 11),
    )
    def test_recent_days_marks_past_empty_day_as_missed(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()
        self.set_habit_created_date(
            habit,
            date(2026, 8, 10),
        )

        response = self.client.get(
            self.habit_detail_url(
                habit.id
            )
        )

        statuses = {
            item["date"]: item["status"]
            for item in response.data["recent_days"]
        }

        self.assertEqual(
            statuses["2026-08-10"],
            "missed",
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 11),
    )
    def test_today_without_record_stays_pending(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        response = self.client.get(
            self.habit_detail_url(
                habit.id
            )
        )

        statuses = {
            item["date"]: item["status"]
            for item in response.data["recent_days"]
        }

        self.assertEqual(
            statuses["2026-08-11"],
            "pending",
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 11),
    )
    def test_days_before_habit_creation_are_not_missed(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()
        self.set_habit_created_date(
            habit,
            date(2026, 8, 10),
        )

        response = self.client.get(
            self.habit_detail_url(
                habit.id
            )
        )

        statuses = {
            item["date"]: item["status"]
            for item in response.data["recent_days"]
        }

        self.assertEqual(
            statuses["2026-08-08"],
            "pending",
        )

        self.assertEqual(
            statuses["2026-08-09"],
            "pending",
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 11),
    )
    def test_list_get_refreshes_persisted_streak(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        self.create_completion(
            habit,
            date(2026, 8, 9),
        )

        habit.streak = 5
        habit.save(
            update_fields=[
                "streak",
            ]
        )

        response = self.client.get(
            self.HABITS_URL
        )

        habit.refresh_from_db()

        self.assertEqual(
            response.data[0]["streak"],
            0,
        )

        self.assertEqual(
            habit.streak,
            0,
        )

    # ---------------------------------------------------------
    # Unique day
    # ---------------------------------------------------------

    def test_one_habit_can_have_only_one_record_per_day(self):
        habit = self.create_habit()

        completion_date = date(
            2026,
            8,
            10,
        )

        self.create_completion(
            habit,
            completion_date,
        )

        with self.assertRaises(
            Exception
        ):
            self.create_completion(
                habit,
                completion_date,
            )

    # ---------------------------------------------------------
    # Archive
    # ---------------------------------------------------------

    def test_archive_habit(self):
        habit = self.create_habit()

        response = self.client.post(
            self.habit_archive_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        habit.refresh_from_db()

        self.assertEqual(
            habit.status,
            Habit.Status.ARCHIVED,
        )

        self.assertEqual(
            response.data["status"],
            Habit.Status.ARCHIVED,
        )

    def test_archiving_twice_is_idempotent(self):
        habit = self.create_habit()

        self.client.post(
            self.habit_archive_url(
                habit.id
            )
        )

        response = self.client.post(
            self.habit_archive_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        habit.refresh_from_db()

        self.assertEqual(
            habit.status,
            Habit.Status.ARCHIVED,
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_archived_habit_cannot_be_completed(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit(
            status_value=(
                Habit.Status.ARCHIVED
            )
        )

        response = self.client.post(
            self.habit_complete_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            HabitCompletion.objects.filter(
                habit=habit
            ).exists()
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_archived_habit_cannot_be_marked_missed(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit(
            status_value=(
                Habit.Status.ARCHIVED
            )
        )

        response = self.client.post(
            self.habit_miss_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            HabitCompletion.objects.filter(
                habit=habit
            ).exists()
        )

    # ---------------------------------------------------------
    # Restore
    # ---------------------------------------------------------

    def test_restore_habit(self):
        habit = self.create_habit(
            status_value=(
                Habit.Status.ARCHIVED
            )
        )

        response = self.client.post(
            self.habit_restore_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        habit.refresh_from_db()

        self.assertEqual(
            habit.status,
            Habit.Status.ACTIVE,
        )

        self.assertEqual(
            response.data["status"],
            Habit.Status.ACTIVE,
        )

    def test_restoring_active_habit_is_idempotent(self):
        habit = self.create_habit()

        response = self.client.post(
            self.habit_restore_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        habit.refresh_from_db()

        self.assertEqual(
            habit.status,
            Habit.Status.ACTIVE,
        )

    # ---------------------------------------------------------
    # Ownership for actions
    # ---------------------------------------------------------

    def test_cannot_archive_other_users_habit(self):
        habit = self.create_habit(
            user=self.other_user
        )

        response = self.client.post(
            self.habit_archive_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_cannot_restore_other_users_habit(self):
        habit = self.create_habit(
            user=self.other_user,
            status_value=(
                Habit.Status.ARCHIVED
            ),
        )

        response = self.client.post(
            self.habit_restore_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_cannot_miss_other_users_habit(self):
        habit = self.create_habit(
            user=self.other_user
        )

        response = self.client.post(
            self.habit_miss_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # ---------------------------------------------------------
    # Brain and Wins integration
    # ---------------------------------------------------------

    def test_create_habit_syncs_brain(self):
        habit = self.create_habit_via_api(
            title="Learn English"
        )

        brain_habits = self.get_brain_habits()

        self.assertEqual(
            len(brain_habits),
            1,
        )

        self.assertEqual(
            brain_habits[0],
            {
                "id": habit.id,
                "title": "Learn English",
                "trigger": "After breakfast",
                "action": "Read one page",
                "reward": "Make coffee",
                "status": Habit.Status.ACTIVE,
                "streak": 0,
                "today_status": "pending",
                "consecutive_misses": 0,
            },
        )

    def test_patch_habit_syncs_brain(self):
        habit = self.create_habit_via_api()

        response = self.client.patch(
            self.habit_detail_url(
                habit.id
            ),
            {
                "title": "Updated habit",
                "action": "Read ten pages",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        brain_habit = self.get_brain_habits()[0]

        self.assertEqual(
            brain_habit["title"],
            "Updated habit",
        )

        self.assertEqual(
            brain_habit["action"],
            "Read ten pages",
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_complete_habit_syncs_brain(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        response = self.client.post(
            self.habit_complete_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        habit.refresh_from_db()
        brain_habit = self.get_brain_habits()[0]

        self.assertEqual(
            habit.streak,
            1,
        )

        self.assertEqual(
            brain_habit["streak"],
            1,
        )

        self.assertEqual(
            brain_habit["today_status"],
            HabitCompletion.Status.COMPLETED,
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_miss_habit_syncs_brain(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        response = self.client.post(
            self.habit_miss_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        brain_habit = self.get_brain_habits()[0]

        self.assertEqual(
            brain_habit["streak"],
            0,
        )

        self.assertEqual(
            brain_habit["today_status"],
            HabitCompletion.Status.MISSED,
        )

        self.assertEqual(
            brain_habit["consecutive_misses"],
            1,
        )

    def test_archive_and_restore_habit_sync_brain(self):
        habit = self.create_habit_via_api()

        archive_response = self.client.post(
            self.habit_archive_url(
                habit.id
            )
        )

        self.assertEqual(
            archive_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            self.get_brain_habits(),
            [],
        )

        restore_response = self.client.post(
            self.habit_restore_url(
                habit.id
            )
        )

        self.assertEqual(
            restore_response.status_code,
            status.HTTP_200_OK,
        )

        brain_habits = self.get_brain_habits()

        self.assertEqual(
            len(brain_habits),
            1,
        )

        self.assertEqual(
            brain_habits[0]["id"],
            habit.id,
        )

        self.assertEqual(
            brain_habits[0]["status"],
            Habit.Status.ACTIVE,
        )

    def test_delete_habit_removes_it_from_brain(self):
        deleted_habit = self.create_habit_via_api(
            title="Delete me"
        )

        remaining_habit = self.create_habit_via_api(
            title="Keep me"
        )

        response = self.client.delete(
            self.habit_detail_url(
                deleted_habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        brain_habits = self.get_brain_habits()

        self.assertEqual(
            [
                brain_habit["id"]
                for brain_habit in brain_habits
            ],
            [remaining_habit.id],
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_streak_milestone_creates_automatic_win(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()
        first_day = date(2026, 8, 4)

        self.set_habit_created_date(
            habit,
            first_day,
        )

        for offset in range(6):
            self.create_completion(
                habit,
                first_day
                + timedelta(days=offset),
            )

        response = self.client.post(
            self.habit_complete_url(
                habit.id
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        habit.refresh_from_db()

        self.assertEqual(
            habit.streak,
            7,
        )

        win = Win.objects.get(
            user=self.user,
            source=Win.HABIT,
        )

        self.assertEqual(
            win.event_key,
            f"habit_streak:{habit.id}:7",
        )

        self.assertEqual(
            win.size,
            Win.SMALL,
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_streak_milestone_win_is_idempotent(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()
        first_day = date(2026, 8, 4)

        self.set_habit_created_date(
            habit,
            first_day,
        )

        for offset in range(6):
            self.create_completion(
                habit,
                first_day
                + timedelta(days=offset),
            )

        self.client.post(
            self.habit_complete_url(
                habit.id
            )
        )

        self.client.post(
            self.habit_complete_url(
                habit.id
            )
        )

        self.assertEqual(
            Win.objects.filter(
                user=self.user,
                event_key=(
                    f"habit_streak:{habit.id}:7"
                ),
            ).count(),
            1,
        )

    @patch(
        "django.utils.timezone.localdate",
        return_value=date(2026, 8, 10),
    )
    def test_non_milestone_actions_do_not_create_win(
        self,
        mocked_localdate,
    ):
        habit = self.create_habit()

        self.client.patch(
            self.habit_detail_url(
                habit.id
            ),
            {
                "title": "Updated habit",
            },
            format="json",
        )

        self.client.post(
            self.habit_miss_url(
                habit.id
            )
        )

        self.client.post(
            self.habit_archive_url(
                habit.id
            )
        )

        self.client.post(
            self.habit_restore_url(
                habit.id
            )
        )

        self.client.post(
            self.habit_complete_url(
                habit.id
            )
        )

        self.assertEqual(
            Win.objects.filter(
                user=self.user,
                source=Win.HABIT,
            ).count(),
            0,
        )
