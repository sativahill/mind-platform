import json
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User
from wins.models import Win

from .ai_service import build_suggestion_key
from .models import DailyLog, DailyLogSuggestion


class DailyLogSuggestionFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="daily-log-owner",
            email="daily-log-owner@example.com",
            password="test-password",
        )
        self.other_user = User.objects.create_user(
            username="daily-log-other",
            email="daily-log-other@example.com",
            password="test-password",
        )
        self.daily_log = DailyLog.objects.create(
            user=self.user,
            date=date(2026, 7, 28),
            content="I completed an important task.",
        )
        self.client.force_authenticate(
            user=self.user
        )

    def suggestion_payload(
        self,
        *,
        title="Completed an important task",
        description="",
        size=DailyLogSuggestion.SIZE_MEDIUM,
    ):
        return {
            "suggestion_type": (
                DailyLogSuggestion.TYPE_WIN
            ),
            "title": title,
            "description": description,
            "size": size,
            "suggestion_key": (
                build_suggestion_key(
                    suggestion_type=(
                        DailyLogSuggestion
                        .TYPE_WIN
                    ),
                    title=title,
                )
            ),
        }

    def create_suggestion(
        self,
        *,
        title="Completed an important task",
        description="",
        size=DailyLogSuggestion.SIZE_MEDIUM,
        suggestion_status=(
            DailyLogSuggestion.STATUS_PENDING
        ),
    ):
        payload = self.suggestion_payload(
            title=title,
            description=description,
            size=size,
        )

        return DailyLogSuggestion.objects.create(
            daily_log=self.daily_log,
            status=suggestion_status,
            **payload,
        )

    def analyze_url(self, daily_log=None):
        selected_log = (
            daily_log or self.daily_log
        )
        return (
            f"{reverse('daily-logs')}"
            f"?id={selected_log.id}"
            "&action=analyze"
        )

    def suggestion_action_url(
        self,
        suggestion,
        action,
    ):
        return (
            f"{reverse('daily-logs')}"
            f"?suggestion_id={suggestion.id}"
            f"&action={action}"
        )

    @patch(
        "daily_logs.ai_service."
        "request_gemini_analysis"
    )
    def test_analyze_returns_empty_suggestions(
        self,
        mock_gemini,
    ):
        mock_gemini.return_value = []

        response = self.client.post(
            self.analyze_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["suggestions"],
            [],
        )
        self.assertEqual(
            response.data["suggestions_count"],
            0,
        )
        self.assertFalse(
            DailyLogSuggestion.objects.exists()
        )

    @patch(
        "daily_logs.ai_service."
        "request_gemini_analysis"
    )
    def test_analyze_returns_one_valid_win(
        self,
        mock_gemini,
    ):
        mock_gemini.return_value = [
            self.suggestion_payload()
        ]

        response = self.client.post(
            self.analyze_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["suggestions_count"],
            1,
        )

        suggestion = (
            DailyLogSuggestion.objects.get()
        )
        self.assertEqual(
            suggestion.suggestion_type,
            DailyLogSuggestion.TYPE_WIN,
        )
        self.assertEqual(
            suggestion.status,
            DailyLogSuggestion.STATUS_PENDING,
        )

    @override_settings(
        GEMINI_API_KEY="test-gemini-key"
    )
    @patch("daily_logs.ai_service.genai.Client")
    def test_invalid_gemini_json_returns_503(
        self,
        mock_client_class,
    ):
        mock_client = (
            mock_client_class.return_value
        )
        mock_client.models.generate_content.return_value = (
            SimpleNamespace(
                text="{invalid-json"
            )
        )

        response = self.client.post(
            self.analyze_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        self.assertTrue(
            response.data["daily_log_saved"]
        )
        self.assertFalse(
            DailyLogSuggestion.objects.exists()
        )

    @override_settings(
        GEMINI_API_KEY="test-gemini-key"
    )
    @patch("daily_logs.ai_service.genai.Client")
    def test_duplicate_suggestions_in_one_response_are_removed(
        self,
        mock_client_class,
    ):
        mock_client = (
            mock_client_class.return_value
        )
        mock_client.models.generate_content.return_value = (
            SimpleNamespace(
                text=json.dumps(
                    {
                        "suggestions": [
                            {
                                "type": "win",
                                "title": (
                                    "Finished the report"
                                ),
                                "description": (
                                    "First wording"
                                ),
                                "size": "medium",
                            },
                            {
                                "type": "win",
                                "title": (
                                    "Finished the report!"
                                ),
                                "description": (
                                    "Changed wording"
                                ),
                                "size": "large",
                            },
                        ]
                    }
                )
            )
        )

        response = self.client.post(
            self.analyze_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["suggestions_count"],
            1,
        )
        self.assertEqual(
            DailyLogSuggestion.objects.count(),
            1,
        )

    @patch(
        "daily_logs.ai_service."
        "request_gemini_analysis"
    )
    def test_repeated_analysis_does_not_recreate_accepted_suggestion(
        self,
        mock_gemini,
    ):
        original = self.suggestion_payload(
            title="Finished the report",
            description="Original detail",
            size=DailyLogSuggestion.SIZE_MEDIUM,
        )
        changed = self.suggestion_payload(
            title="Finished the report",
            description="Different detail",
            size=DailyLogSuggestion.SIZE_LARGE,
        )
        mock_gemini.side_effect = [
            [original],
            [changed],
        ]

        first_analysis = self.client.post(
            self.analyze_url()
        )
        suggestion_id = (
            first_analysis.data[
                "suggestions"
            ][0]["id"]
        )
        suggestion = (
            DailyLogSuggestion.objects.get(
                id=suggestion_id
            )
        )
        self.client.post(
            self.suggestion_action_url(
                suggestion,
                "accept",
            )
        )

        second_analysis = self.client.post(
            self.analyze_url()
        )

        self.assertEqual(
            second_analysis.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            second_analysis.data[
                "suggestions_count"
            ],
            0,
        )
        self.assertEqual(
            DailyLogSuggestion.objects.count(),
            1,
        )
        self.assertEqual(
            Win.objects.count(),
            1,
        )

    @patch(
        "daily_logs.ai_service."
        "request_gemini_analysis"
    )
    def test_size_and_description_change_do_not_create_duplicate(
        self,
        mock_gemini,
    ):
        accepted = self.create_suggestion(
            title="Completed the course",
            description="Medium interpretation",
            size=DailyLogSuggestion.SIZE_MEDIUM,
            suggestion_status=(
                DailyLogSuggestion
                .STATUS_ACCEPTED
            ),
        )
        changed = self.suggestion_payload(
            title="Completed the course",
            description="Large interpretation",
            size=DailyLogSuggestion.SIZE_LARGE,
        )
        mock_gemini.return_value = [changed]

        response = self.client.post(
            self.analyze_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["suggestions_count"],
            0,
        )
        self.assertEqual(
            DailyLogSuggestion.objects.count(),
            1,
        )
        accepted.refresh_from_db()
        self.assertEqual(
            accepted.status,
            DailyLogSuggestion.STATUS_ACCEPTED,
        )

    def test_accept_creates_one_daily_log_win_and_updates_brain(
        self,
    ):
        suggestion = self.create_suggestion(
            size=DailyLogSuggestion.SIZE_LARGE
        )

        response = self.client.post(
            self.suggestion_action_url(
                suggestion,
                "accept",
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            response.data["win_created"]
        )

        win = Win.objects.get()
        self.assertEqual(
            win.source,
            Win.DAILY_LOG,
        )
        self.assertEqual(
            win.date,
            self.daily_log.date,
        )
        self.assertEqual(
            win.event_key,
            (
                f"daily_log:{self.daily_log.id}:"
                f"win:{suggestion.suggestion_key}"
            ),
        )

        self.user.brain.refresh_from_db()
        brain_data = self.user.brain.data
        self.assertEqual(
            len(brain_data["history"]["wins"]),
            1,
        )
        self.assertEqual(
            brain_data["progress"]["wins_count"],
            1,
        )
        self.assertEqual(
            brain_data[
                "progress"
            ]["large_wins_count"],
            1,
        )

    def test_repeated_accept_returns_existing_win_without_duplicate(
        self,
    ):
        suggestion = self.create_suggestion()
        url = self.suggestion_action_url(
            suggestion,
            "accept",
        )

        first_response = self.client.post(url)
        second_response = self.client.post(url)

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            first_response.data["win_created"]
        )
        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertFalse(
            second_response.data["win_created"]
        )
        self.assertEqual(
            first_response.data["win"]["id"],
            second_response.data["win"]["id"],
        )
        self.assertEqual(
            Win.objects.count(),
            1,
        )

        suggestion.refresh_from_db()
        self.assertEqual(
            suggestion.status,
            DailyLogSuggestion.STATUS_ACCEPTED,
        )
        self.user.brain.refresh_from_db()
        self.assertEqual(
            len(
                self.user.brain.data[
                    "history"
                ]["wins"]
            ),
            1,
        )

    def test_dismiss_and_repeated_dismiss_are_safe(
        self,
    ):
        suggestion = self.create_suggestion()
        url = self.suggestion_action_url(
            suggestion,
            "dismiss",
        )

        first_response = self.client.post(url)
        second_response = self.client.post(url)

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
        )
        suggestion.refresh_from_db()
        self.assertEqual(
            suggestion.status,
            DailyLogSuggestion.STATUS_DISMISSED,
        )
        self.assertFalse(
            Win.objects.exists()
        )

    def test_accept_after_dismiss_returns_409(
        self,
    ):
        suggestion = self.create_suggestion(
            suggestion_status=(
                DailyLogSuggestion
                .STATUS_DISMISSED
            )
        )

        response = self.client.post(
            self.suggestion_action_url(
                suggestion,
                "accept",
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
        )
        self.assertFalse(
            Win.objects.exists()
        )

    def test_dismiss_after_accept_returns_409(
        self,
    ):
        suggestion = self.create_suggestion(
            suggestion_status=(
                DailyLogSuggestion
                .STATUS_ACCEPTED
            )
        )

        response = self.client.post(
            self.suggestion_action_url(
                suggestion,
                "dismiss",
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
        )
        suggestion.refresh_from_db()
        self.assertEqual(
            suggestion.status,
            DailyLogSuggestion.STATUS_ACCEPTED,
        )

    @patch(
        "daily_logs.ai_service."
        "request_gemini_analysis"
    )
    def test_another_user_cannot_access_daily_log_or_suggestion(
        self,
        mock_gemini,
    ):
        suggestion = self.create_suggestion()
        self.client.force_authenticate(
            user=self.other_user
        )

        analyze_response = self.client.post(
            self.analyze_url()
        )
        list_response = self.client.get(
            (
                f"{reverse('daily-logs')}"
                f"?id={self.daily_log.id}"
                "&action=suggestions"
            )
        )
        accept_response = self.client.post(
            self.suggestion_action_url(
                suggestion,
                "accept",
            )
        )
        dismiss_response = self.client.post(
            self.suggestion_action_url(
                suggestion,
                "dismiss",
            )
        )

        self.assertEqual(
            analyze_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            list_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            accept_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            dismiss_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        mock_gemini.assert_not_called()
        self.assertFalse(
            Win.objects.exists()
        )

    @patch(
        "daily_logs.ai_service."
        "request_gemini_analysis"
    )
    def test_edit_clears_pending_and_preserves_resolved_suggestions(
        self,
        mock_gemini,
    ):
        pending = self.create_suggestion(
            title="Old pending event"
        )
        accepted = self.create_suggestion(
            title="Accepted event",
            suggestion_status=(
                DailyLogSuggestion
                .STATUS_ACCEPTED
            ),
        )
        dismissed = self.create_suggestion(
            title="Dismissed event",
            suggestion_status=(
                DailyLogSuggestion
                .STATUS_DISMISSED
            ),
        )

        edit_response = self.client.patch(
            (
                f"{reverse('daily-logs')}"
                f"?id={self.daily_log.id}"
            ),
            {
                "content": (
                    "Updated content with a new event."
                )
            },
            format="json",
        )

        self.assertEqual(
            edit_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertFalse(
            DailyLogSuggestion.objects.filter(
                id=pending.id
            ).exists()
        )
        self.assertTrue(
            DailyLogSuggestion.objects.filter(
                id=accepted.id,
                status=(
                    DailyLogSuggestion
                    .STATUS_ACCEPTED
                ),
            ).exists()
        )
        self.assertTrue(
            DailyLogSuggestion.objects.filter(
                id=dismissed.id,
                status=(
                    DailyLogSuggestion
                    .STATUS_DISMISSED
                ),
            ).exists()
        )

        mock_gemini.return_value = [
            self.suggestion_payload(
                title="Accepted event",
                description="Changed description",
                size=(
                    DailyLogSuggestion
                    .SIZE_LARGE
                ),
            ),
            self.suggestion_payload(
                title="Dismissed event",
                description="Changed description",
                size=(
                    DailyLogSuggestion
                    .SIZE_LARGE
                ),
            ),
            self.suggestion_payload(
                title="Brand new event",
            ),
        ]

        analyze_response = self.client.post(
            self.analyze_url()
        )

        self.assertEqual(
            analyze_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            analyze_response.data[
                "suggestions_count"
            ],
            1,
        )
        self.assertEqual(
            analyze_response.data[
                "suggestions"
            ][0]["title"],
            "Brand new event",
        )
        self.assertEqual(
            DailyLogSuggestion.objects.count(),
            3,
        )
