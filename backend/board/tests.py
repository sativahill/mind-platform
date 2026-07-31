from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from goals.models import Goal
from users.models import User
from wins.models import Win

from .models import BoardTask


class BoardTaskAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="board-owner",
            email="board-owner@example.com",
            password="test-password",
        )

        self.other_user = User.objects.create_user(
            username="other-board-user",
            email="other-board-user@example.com",
            password="test-password",
        )

        self.goal = Goal.objects.create(
            user=self.user,
            title="Finish Goals module",
            why_it_matters="It moves PROJECT forward.",
        )

        self.other_goal = Goal.objects.create(
            user=self.other_user,
            title="Private goal",
        )

        self.client.force_authenticate(
            user=self.user
        )

        self.list_url = reverse(
            "board"
        )

    def detail_url(self, task):
        return reverse(
            "board-detail",
            kwargs={
                "task_id": task.id,
            },
        )

    def test_user_can_create_task_for_own_goal(self):
        response = self.client.post(
            self.list_url,
            {
                "goal": self.goal.id,
                "title": "Write Board tests",
                "description": (
                    "Cover the Board and Goals integration."
                ),
                "status": BoardTask.TODO,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            BoardTask.objects.count(),
            1,
        )

        task = BoardTask.objects.get()

        self.assertEqual(
            task.goal,
            self.goal,
        )

        self.assertEqual(
            task.title,
            "Write Board tests",
        )

        self.assertEqual(
            task.status,
            BoardTask.TODO,
        )

    def test_user_cannot_create_task_for_another_users_goal(
        self,
    ):
        response = self.client.post(
            self.list_url,
            {
                "goal": self.other_goal.id,
                "title": "Unauthorized task",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertEqual(
            BoardTask.objects.count(),
            0,
        )

    def test_user_only_sees_tasks_from_own_goals(self):
        own_task = BoardTask.objects.create(
            goal=self.goal,
            title="Own task",
        )

        BoardTask.objects.create(
            goal=self.other_goal,
            title="Other user's task",
        )

        response = self.client.get(
            self.list_url
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
            own_task.id,
        )

    def test_creating_first_incomplete_task_keeps_progress_zero(
        self,
    ):
        self.goal.progress = 75
        self.goal.save(
            update_fields=[
                "progress",
            ]
        )

        response = self.client.post(
            self.list_url,
            {
                "goal": self.goal.id,
                "title": "Incomplete task",
                "status": BoardTask.TODO,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.goal.refresh_from_db()

        self.assertEqual(
            self.goal.progress,
            0,
        )

        self.assertEqual(
            self.goal.status,
            Goal.ACTIVE,
        )

    def test_creating_completed_task_completes_goal(
        self,
    ):
        response = self.client.post(
            self.list_url,
            {
                "goal": self.goal.id,
                "title": "Only required task",
                "status": BoardTask.DONE,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.goal.refresh_from_db()

        self.assertEqual(
            self.goal.progress,
            100,
        )

        self.assertEqual(
            self.goal.status,
            Goal.COMPLETED,
        )

        self.assertIsNotNone(
            self.goal.completed_at,
        )

    def test_user_can_change_task_status(self):
        task = BoardTask.objects.create(
            goal=self.goal,
            title="Move task",
            status=BoardTask.TODO,
        )

        response = self.client.patch(
            self.detail_url(task),
            {
                "status": BoardTask.IN_PROGRESS,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        task.refresh_from_db()

        self.assertEqual(
            task.status,
            BoardTask.IN_PROGRESS,
        )

    def test_invalid_task_status_is_rejected(self):
        task = BoardTask.objects.create(
            goal=self.goal,
            title="Protected task",
        )

        response = self.client.patch(
            self.detail_url(task),
            {
                "status": "unknown",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        task.refresh_from_db()

        self.assertEqual(
            task.status,
            BoardTask.TODO,
        )

    def test_user_cannot_update_another_users_task(
        self,
    ):
        task = BoardTask.objects.create(
            goal=self.other_goal,
            title="Private task",
        )

        response = self.client.patch(
            self.detail_url(task),
            {
                "status": BoardTask.DONE,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        task.refresh_from_db()

        self.assertEqual(
            task.status,
            BoardTask.TODO,
        )

    def test_task_status_updates_goal_progress(self):
        first_task = BoardTask.objects.create(
            goal=self.goal,
            title="First task",
            status=BoardTask.TODO,
        )

        BoardTask.objects.create(
            goal=self.goal,
            title="Second task",
            status=BoardTask.TODO,
        )

        response = self.client.patch(
            self.detail_url(first_task),
            {
                "status": BoardTask.DONE,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.goal.refresh_from_db()

        self.assertEqual(
            self.goal.progress,
            50,
        )

        self.assertEqual(
            self.goal.status,
            Goal.ACTIVE,
        )

    def test_finishing_last_task_completes_goal(self):
        first_task = BoardTask.objects.create(
            goal=self.goal,
            title="First task",
            status=BoardTask.DONE,
        )

        second_task = BoardTask.objects.create(
            goal=self.goal,
            title="Second task",
            status=BoardTask.TODO,
        )

        self.assertEqual(
            first_task.status,
            BoardTask.DONE,
        )

        response = self.client.patch(
            self.detail_url(second_task),
            {
                "status": BoardTask.DONE,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.goal.refresh_from_db()

        self.assertEqual(
            self.goal.progress,
            100,
        )

        self.assertEqual(
            self.goal.status,
            Goal.COMPLETED,
        )

        self.assertIsNotNone(
            self.goal.completed_at,
        )

    def test_goal_completion_creates_single_win(self):
        task = BoardTask.objects.create(
            goal=self.goal,
            title="Complete the goal",
            status=BoardTask.TODO,
        )

        detail_url = self.detail_url(
            task
        )

        first_response = self.client.patch(
            detail_url,
            {
                "status": BoardTask.DONE,
            },
            format="json",
        )

        second_response = self.client.patch(
            detail_url,
            {
                "status": BoardTask.DONE,
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
        )

        wins = Win.objects.filter(
            user=self.user,
            source=Win.GOAL,
            source_id=str(self.goal.id),
        )

        self.assertEqual(
            wins.count(),
            1,
        )

        win = wins.get()

        self.assertEqual(
            win.event_key,
            f"goal_completed:{self.goal.id}",
        )

    def test_goal_completion_updates_brain(self):
        task = BoardTask.objects.create(
            goal=self.goal,
            title="Complete integration",
            status=BoardTask.TODO,
        )

        response = self.client.patch(
            self.detail_url(task),
            {
                "status": BoardTask.DONE,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.brain.refresh_from_db()

        brain_data = self.user.brain.data

        completed_goals = brain_data[
            "progress"
        ]["goals"]["completed"]

        self.assertEqual(
            len(completed_goals),
            1,
        )

        self.assertEqual(
            completed_goals[0]["id"],
            self.goal.id,
        )

        self.assertEqual(
            brain_data[
                "progress"
            ]["goals"]["total_completed"],
            1,
        )

        self.assertEqual(
            brain_data[
                "progress"
            ]["wins_count"],
            1,
        )

        self.assertEqual(
            brain_data[
                "history"
            ]["wins"][0]["source"],
            Win.GOAL,
        )

        self.assertIsNone(
            brain_data[
                "context"
            ]["primary_goal"],
        )