from django.urls import Resolver404, resolve
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


class V1APISurfaceTests(APITestCase):
    CORE_GET_PATHS = (
        "/api/brain/",
        "/api/home/",
        "/api/daily-logs/",
        "/api/wins/",
        "/api/chats/",
        "/api/goals/",
        "/api/board/",
        "/api/habits/",
    )
    CORE_POST_PATHS = (
        "/api/token/",
        "/api/token/refresh/",
        "/api/register/",
    )
    FUTURE_PATHS = (
        "/api/analytics/reports/",
        "/api/analytics/messages/",
        "/api/finance/",
        "/api/library/",
        "/api/notifications/",
        "/api/progress-photos/",
    )

    def setUp(self):
        self.user = User.objects.create_user(
            username="release-surface-user",
            email="release-surface@example.com",
            password="test-password",
        )
        self.client.force_authenticate(
            user=self.user
        )

    def test_core_routes_are_resolved(self):
        for path in (
            *self.CORE_GET_PATHS,
            *self.CORE_POST_PATHS,
        ):
            with self.subTest(path=path):
                self.assertIsNotNone(resolve(path))

    def test_core_routes_remain_http_reachable(self):
        for path in self.CORE_GET_PATHS:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertNotEqual(
                    response.status_code,
                    status.HTTP_404_NOT_FOUND,
                )

        for path in self.CORE_POST_PATHS:
            with self.subTest(path=path):
                response = self.client.post(
                    path,
                    {},
                    format="json",
                )
                self.assertNotEqual(
                    response.status_code,
                    status.HTTP_404_NOT_FOUND,
                )

    def test_future_routes_are_not_resolved(self):
        for path in self.FUTURE_PATHS:
            with self.subTest(path=path):
                with self.assertRaises(Resolver404):
                    resolve(path)

    def test_future_routes_return_404(self):
        for path in self.FUTURE_PATHS:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(
                    response.status_code,
                    status.HTTP_404_NOT_FOUND,
                )
