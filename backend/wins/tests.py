from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from daily_logs.ai_service import (
    build_suggestion_key,
)
from daily_logs.models import DailyLog
from users.models import User

from .models import Win
from .services import (
    create_automatic_win,
    create_daily_log_win,
    create_manual_win,
)


class WinBrainSynchronizationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="wins-owner",
            email="wins-owner@example.com",
            password="test-password",
        )
        self.client.force_authenticate(
            user=self.user
        )

    def test_deleting_win_rebuilds_brain(self):
        older = create_manual_win(
            user=self.user,
            title="Older small win",
            date="2026-07-20",
            size=Win.SMALL,
        )
        newer = create_manual_win(
            user=self.user,
            title="Newer large win",
            date="2026-07-29",
            size=Win.LARGE,
        )

        response = self.client.delete(
            (
                f"{reverse('wins')}"
                f"?id={newer.id}"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.user.brain.refresh_from_db()
        brain_data = self.user.brain.data
        self.assertEqual(
            [
                item["id"]
                for item
                in brain_data["history"]["wins"]
            ],
            [older.id],
        )
        self.assertEqual(
            brain_data[
                "context"
            ]["last_win"]["id"],
            older.id,
        )
        self.assertEqual(
            brain_data["progress"]["wins_count"],
            1,
        )
        self.assertEqual(
            brain_data[
                "progress"
            ]["large_wins_count"],
            0,
        )

    def test_editing_old_win_keeps_actual_last_win(
        self,
    ):
        older = create_manual_win(
            user=self.user,
            title="Older win",
            date="2026-07-20",
            size=Win.SMALL,
        )
        newer = create_manual_win(
            user=self.user,
            title="Actual last win",
            date="2026-07-29",
            size=Win.MEDIUM,
        )

        response = self.client.patch(
            (
                f"{reverse('wins')}"
                f"?id={older.id}"
            ),
            {
                "title": "Edited older win",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.user.brain.refresh_from_db()
        brain_data = self.user.brain.data
        self.assertEqual(
            brain_data[
                "context"
            ]["last_win"]["id"],
            newer.id,
        )
        history = brain_data["history"]["wins"]
        self.assertEqual(
            [
                item["id"]
                for item in history
            ].count(older.id),
            1,
        )
        edited_item = next(
            item
            for item in history
            if item["id"] == older.id
        )
        self.assertEqual(
            edited_item["title"],
            "Edited older win",
        )

    def test_daily_log_win_uses_stable_suggestion_key(
        self,
    ):
        daily_log = DailyLog.objects.create(
            user=self.user,
            date=date(2026, 7, 28),
            content="I completed the release.",
        )
        suggestion_key = build_suggestion_key(
            suggestion_type="win",
            title="Completed the release",
        )

        win, created = create_daily_log_win(
            daily_log=daily_log,
            title="Completed the release",
            suggestion_key=suggestion_key,
            suggestion_id="42",
            size=Win.LARGE,
        )

        self.assertTrue(created)
        self.assertEqual(
            win.event_key,
            (
                f"daily_log:{daily_log.id}:"
                f"win:{suggestion_key}"
            ),
        )

    def test_daily_log_win_reuses_legacy_event_key(
        self,
    ):
        daily_log = DailyLog.objects.create(
            user=self.user,
            date=date(2026, 7, 28),
            content="I completed the release.",
        )
        legacy_key = (
            f"daily_log:{daily_log.id}:win:42"
        )
        legacy_win, _ = create_automatic_win(
            user=self.user,
            title="Completed the release",
            source=Win.DAILY_LOG,
            event_key=legacy_key,
            source_id=str(daily_log.id),
            date=daily_log.date,
            size=Win.LARGE,
        )

        returned_win, created = (
            create_daily_log_win(
                daily_log=daily_log,
                title="Completed the release",
                suggestion_key=(
                    build_suggestion_key(
                        suggestion_type="win",
                        title=(
                            "Completed the release"
                        ),
                    )
                ),
                suggestion_id="42",
                size=Win.LARGE,
            )
        )

        self.assertFalse(created)
        self.assertEqual(
            returned_win.id,
            legacy_win.id,
        )
        self.assertEqual(
            Win.objects.count(),
            1,
        )
