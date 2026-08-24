from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from board.models import (
    BoardTask,
    BoardTaskDependency,
)
from board.services import sync_brain_board
from users.models import User
from wins.models import Win

from .models import Goal
from .services import (
    complete_goal,
    recalculate_goal_progress,
)


class GoalAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="goals-owner",
            email="goals-owner@example.com",
            password="test-password",
        )
        self.other_user = User.objects.create_user(
            username="other-user",
            email="other-user@example.com",
            password="test-password",
        )

        self.client.force_authenticate(
            user=self.user
        )

        self.url = reverse("goals")

    def test_user_can_create_goal(self):
        response = self.client.post(
            self.url,
            {
                "title": "Pass IELTS",
                "description": (
                    "Reach the required overall score."
                ),
                "why_it_matters": (
                    "It is required for university."
                ),
                "previous_obstacles": (
                    "Weak reading and inconsistent practice."
                ),
                "target_date": "2026-10-31",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            Goal.objects.count(),
            1,
        )

        goal = Goal.objects.get()

        self.assertEqual(
            goal.user,
            self.user,
        )
        self.assertEqual(
            goal.title,
            "Pass IELTS",
        )
        self.assertEqual(
            goal.target_date,
            date(2026, 10, 31),
        )
        self.assertEqual(
            goal.progress,
            0,
        )
        self.assertEqual(
            goal.status,
            Goal.ACTIVE,
        )

    def test_progress_cannot_be_set_from_api(self):
        response = self.client.post(
            self.url,
            {
                "title": "Build PROJECT",
                "progress": 100,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        goal = Goal.objects.get()

        self.assertEqual(
            goal.progress,
            0,
        )

    def test_goal_title_is_trimmed(self):
        response = self.client.post(
            self.url,
            {
                "title": "   Finish MVP   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            Goal.objects.get().title,
            "Finish MVP",
        )

    def test_empty_goal_title_is_rejected(self):
        response = self.client.post(
            self.url,
            {
                "title": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            Goal.objects.count(),
            0,
        )

    def test_user_only_sees_own_goals(self):
        own_goal = Goal.objects.create(
            user=self.user,
            title="Own goal",
        )
        Goal.objects.create(
            user=self.other_user,
            title="Other goal",
        )

        response = self.client.get(
            self.url
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
            own_goal.id,
        )

    def test_user_can_filter_goals_by_status(self):
        active_goal = Goal.objects.create(
            user=self.user,
            title="Active goal",
        )
        Goal.objects.create(
            user=self.user,
            title="Archived goal",
            status=Goal.ARCHIVED,
        )

        response = self.client.get(
            f"{self.url}?status=active"
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
            active_goal.id,
        )

    def test_invalid_status_filter_is_rejected(self):
        response = self.client.get(
            f"{self.url}?status=unknown"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_user_can_retrieve_single_goal(self):
        goal = Goal.objects.create(
            user=self.user,
            title="Single goal",
        )

        response = self.client.get(
            f"{self.url}?id={goal.id}"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["id"],
            goal.id,
        )

    def test_user_cannot_retrieve_another_users_goal(
        self,
    ):
        goal = Goal.objects.create(
            user=self.other_user,
            title="Private goal",
        )

        response = self.client.get(
            f"{self.url}?id={goal.id}"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_user_can_update_goal(self):
        goal = Goal.objects.create(
            user=self.user,
            title="Old title",
        )

        response = self.client.patch(
            f"{self.url}?id={goal.id}",
            {
                "title": "Updated title",
                "why_it_matters": (
                    "This is important."
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        goal.refresh_from_db()

        self.assertEqual(
            goal.title,
            "Updated title",
        )
        self.assertEqual(
            goal.why_it_matters,
            "This is important.",
        )

    def test_goal_cannot_be_completed_manually(self):
        goal = Goal.objects.create(
            user=self.user,
            title="Protected goal",
        )

        response = self.client.patch(
            f"{self.url}?id={goal.id}",
            {
                "status": Goal.COMPLETED,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        goal.refresh_from_db()

        self.assertEqual(
            goal.status,
            Goal.ACTIVE,
        )

    def test_user_cannot_update_another_users_goal(
        self,
    ):
        goal = Goal.objects.create(
            user=self.other_user,
            title="Private goal",
        )

        response = self.client.patch(
            f"{self.url}?id={goal.id}",
            {
                "title": "Changed",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        goal.refresh_from_db()

        self.assertEqual(
            goal.title,
            "Private goal",
        )

    def test_deleting_goal_rebuilds_brain(self):
        first_goal = Goal.objects.create(
            user=self.user,
            title="First goal",
        )
        second_goal = Goal.objects.create(
            user=self.user,
            title="Second goal",
        )

        from .services import sync_brain_goals

        sync_brain_goals(
            self.user
        )

        response = self.client.delete(
            f"{self.url}?id={second_goal.id}"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.user.brain.refresh_from_db()

        active_goals = self.user.brain.data[
            "progress"
        ]["goals"]["active"]

        self.assertEqual(
            [
                item["id"]
                for item in active_goals
            ],
            [first_goal.id],
        )

    def test_delete_goal_removes_cascaded_tasks_from_brain(
        self,
    ):
        goal = Goal.objects.create(
            user=self.user,
            title="Temporary goal",
        )

        task = BoardTask.objects.create(
            goal=goal,
            title="Temporary task",
            status=BoardTask.IN_PROGRESS,
            due_date=date(2020, 1, 1),
        )

        sync_brain_board(
            self.user
        )

        response = self.client.delete(
            f"{self.url}?id={goal.id}"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Goal.objects.filter(
                id=goal.id
            ).exists()
        )

        self.assertFalse(
            BoardTask.objects.filter(
                id=task.id
            ).exists()
        )

        self.user.brain.refresh_from_db()
        brain_data = self.user.brain.data

        self.assertEqual(
            brain_data["history"]["board_tasks"],
            [],
        )

        self.assertEqual(
            brain_data["progress"]["board"],
            {
                "total": 0,
                "todo": 0,
                "in_progress": 0,
                "done": 0,
                "blocked": 0,
                "overdue": 0,
            },
        )

        self.assertEqual(
            brain_data["context"]["board"],
            {
                "next_task": None,
                "in_progress_tasks": [],
                "overdue_tasks": [],
                "blocked_tasks": [],
            },
        )

    def test_delete_goal_preserves_and_recalculates_other_state(
        self,
    ):
        deleted_goal = Goal.objects.create(
            user=self.user,
            title="Deleted goal",
        )

        remaining_goal = Goal.objects.create(
            user=self.user,
            title="Remaining goal",
        )

        deleted_task = BoardTask.objects.create(
            goal=deleted_goal,
            title="Deleted task",
            status=BoardTask.IN_PROGRESS,
            priority=BoardTask.PRIORITY_CRITICAL,
            due_date=date(2020, 1, 1),
        )

        remaining_task = BoardTask.objects.create(
            goal=remaining_goal,
            title="Remaining task",
            status=BoardTask.TODO,
        )

        BoardTaskDependency.objects.create(
            task=remaining_task,
            depends_on=deleted_task,
        )

        sync_brain_board(
            self.user
        )

        response = self.client.delete(
            f"{self.url}?id={deleted_goal.id}"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Goal.objects.filter(
                id=deleted_goal.id
            ).exists()
        )

        self.assertTrue(
            Goal.objects.filter(
                id=remaining_goal.id
            ).exists()
        )

        self.assertFalse(
            BoardTask.objects.filter(
                id=deleted_task.id
            ).exists()
        )

        self.assertTrue(
            BoardTask.objects.filter(
                id=remaining_task.id
            ).exists()
        )

        self.user.brain.refresh_from_db()
        brain_data = self.user.brain.data

        board_tasks = brain_data[
            "history"
        ]["board_tasks"]

        self.assertEqual(
            [
                task["id"]
                for task in board_tasks
            ],
            [remaining_task.id],
        )

        board_progress = brain_data[
            "progress"
        ]["board"]

        self.assertEqual(
            board_progress,
            {
                "total": 1,
                "todo": 1,
                "in_progress": 0,
                "done": 0,
                "blocked": 0,
                "overdue": 0,
            },
        )

        board_context = brain_data[
            "context"
        ]["board"]

        self.assertEqual(
            board_context["next_task"]["id"],
            remaining_task.id,
        )

        self.assertEqual(
            board_context["in_progress_tasks"],
            [],
        )

        self.assertEqual(
            board_context["blocked_tasks"],
            [],
        )

        self.assertEqual(
            board_context["overdue_tasks"],
            [],
        )

        active_goals = brain_data[
            "progress"
        ]["goals"]["active"]

        self.assertEqual(
            [
                goal_data["id"]
                for goal_data in active_goals
            ],
            [remaining_goal.id],
        )


class GoalServiceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="goal-service-owner",
            email="goal-service@example.com",
            password="test-password",
        )

        self.goal = Goal.objects.create(
            user=self.user,
            title="Complete PROJECT module",
            description="Finish the Goals module.",
            why_it_matters=(
                "It moves the product forward."
            ),
        )

    def test_progress_is_calculated_from_board_tasks(
        self,
    ):
        BoardTask.objects.create(
            goal=self.goal,
            title="First task",
            status=BoardTask.DONE,
        )
        BoardTask.objects.create(
            goal=self.goal,
            title="Second task",
            status=BoardTask.TODO,
        )

        recalculate_goal_progress(
            self.goal
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

    def test_goal_with_no_tasks_has_zero_progress(
        self,
    ):
        self.goal.progress = 70
        self.goal.save(
            update_fields=["progress"]
        )

        recalculate_goal_progress(
            self.goal
        )

        self.goal.refresh_from_db()

        self.assertEqual(
            self.goal.progress,
            0,
        )

    def test_all_completed_tasks_complete_goal(self):
        BoardTask.objects.create(
            goal=self.goal,
            title="First task",
            status=BoardTask.DONE,
        )
        BoardTask.objects.create(
            goal=self.goal,
            title="Second task",
            status=BoardTask.DONE,
        )

        recalculate_goal_progress(
            self.goal
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

    def test_completed_goal_creates_automatic_win(
        self,
    ):
        complete_goal(
            self.goal
        )

        win = Win.objects.get(
            user=self.user,
            source=Win.GOAL,
            source_id=str(self.goal.id),
        )

        self.assertEqual(
            win.title,
            (
                "Completed goal: "
                "Complete PROJECT module"
            ),
        )
        self.assertEqual(
            win.event_key,
            (
                f"goal_completed:"
                f"{self.goal.id}"
            ),
        )
        self.assertEqual(
            win.size,
            Win.LARGE,
        )

    def test_completing_goal_twice_does_not_duplicate_win(
        self,
    ):
        complete_goal(
            self.goal
        )
        complete_goal(
            self.goal
        )

        self.assertEqual(
            Win.objects.filter(
                user=self.user,
                source=Win.GOAL,
                source_id=str(self.goal.id),
            ).count(),
            1,
        )

    def test_goal_completion_updates_brain(self):
        complete_goal(
            self.goal
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
        self.assertIsNone(
            brain_data[
                "context"
            ]["primary_goal"],
        )

    def test_archived_goal_is_not_recalculated(self):
        self.goal.status = Goal.ARCHIVED
        self.goal.progress = 35
        self.goal.save(
            update_fields=[
                "status",
                "progress",
            ]
        )

        BoardTask.objects.create(
            goal=self.goal,
            title="Completed task",
            status=BoardTask.DONE,
        )

        recalculate_goal_progress(
            self.goal
        )

        self.goal.refresh_from_db()

        self.assertEqual(
            self.goal.status,
            Goal.ARCHIVED,
        )
        self.assertEqual(
            self.goal.progress,
            35,
        )
        self.assertEqual(
            Win.objects.count(),
            0,
        )
