from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from goals.models import Goal
from wins.models import Win

from .models import (
    BoardTask,
    BoardTaskDependency,
)


User = get_user_model()


class BoardTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = self.create_user(
            email="board-owner@example.com",
        )

        self.other_user = self.create_user(
            email="board-other@example.com",
        )

        self.goal = Goal.objects.create(
            user=self.user,
            title="Pass IELTS",
            description="Reach an overall score of 6.5.",
            why_it_matters="Study abroad.",
            previous_obstacles="Inconsistent practice.",
            status=Goal.ACTIVE,
            progress=0,
        )

        self.second_goal = Goal.objects.create(
            user=self.user,
            title="Build PROJECT",
            description="Finish the personal platform.",
            status=Goal.ACTIVE,
            progress=0,
        )

        self.other_goal = Goal.objects.create(
            user=self.other_user,
            title="Other user's goal",
            status=Goal.ACTIVE,
            progress=0,
        )

        self.list_url = reverse(
            "board",
        )

        self.layout_url = reverse(
            "board-layout",
        )

        self.client.force_authenticate(
            user=self.user,
        )

    @staticmethod
    def create_user(
        *,
        email,
    ):
        manager = User.objects

        try:
            return manager.create_user(
                email=email,
                password="StrongPass123!",
            )
        except TypeError:
            return manager.create_user(
                username=email,
                email=email,
                password="StrongPass123!",
            )

    @staticmethod
    def task_detail_url(
        task,
    ):
        return reverse(
            "board-detail",
            kwargs={
                "task_id": task.id,
            },
        )

    def create_task(
        self,
        *,
        goal=None,
        title="Read one IELTS passage",
        description="Complete it under timed conditions.",
        task_status=BoardTask.TODO,
        priority=BoardTask.PRIORITY_MEDIUM,
        importance=BoardTask.IMPORTANCE_SMALL,
        due_date=None,
        position_x=5000,
        position_y=5000,
        sort_order=0,
        source=BoardTask.SOURCE_MANUAL,
    ):
        return BoardTask.objects.create(
            goal=goal or self.goal,
            title=title,
            description=description,
            status=task_status,
            priority=priority,
            importance=importance,
            due_date=due_date,
            position_x=position_x,
            position_y=position_y,
            sort_order=sort_order,
            source=source,
        )


class BoardTaskModelTests(
    BoardTestBase
):
    def test_task_defaults(self):
        task = BoardTask.objects.create(
            goal=self.goal,
            title="Review vocabulary",
        )

        self.assertEqual(
            task.status,
            BoardTask.TODO,
        )

        self.assertEqual(
            task.priority,
            BoardTask.PRIORITY_MEDIUM,
        )

        self.assertEqual(
            task.importance,
            BoardTask.IMPORTANCE_SMALL,
        )

        self.assertEqual(
            task.source,
            BoardTask.SOURCE_MANUAL,
        )

        self.assertEqual(
            task.position_x,
            5000,
        )

        self.assertEqual(
            task.position_y,
            5000,
        )

        self.assertEqual(
            task.sort_order,
            0,
        )

        self.assertIsNone(
            task.completed_at,
        )

    def test_task_string_representation(self):
        task = self.create_task(
            title="Write an essay",
        )

        self.assertEqual(
            str(task),
            "Write an essay",
        )

    def test_task_is_not_blocked_without_dependencies(
        self,
    ):
        task = self.create_task()

        self.assertFalse(
            task.is_blocked
        )

    def test_task_is_blocked_by_unfinished_dependency(
        self,
    ):
        dependency = self.create_task(
            title="Learn essay structure",
        )

        task = self.create_task(
            title="Write complete essay",
        )

        BoardTaskDependency.objects.create(
            task=task,
            depends_on=dependency,
        )

        self.assertTrue(
            task.is_blocked
        )

    def test_task_is_unblocked_when_dependencies_are_done(
        self,
    ):
        dependency = self.create_task(
            title="Learn essay structure",
            task_status=BoardTask.DONE,
        )

        task = self.create_task(
            title="Write complete essay",
        )

        BoardTaskDependency.objects.create(
            task=task,
            depends_on=dependency,
        )

        self.assertFalse(
            task.is_blocked
        )

    def test_duplicate_dependency_is_rejected_by_database(
        self,
    ):
        dependency = self.create_task(
            title="Prepare outline",
        )

        task = self.create_task(
            title="Write essay",
        )

        BoardTaskDependency.objects.create(
            task=task,
            depends_on=dependency,
        )

        with self.assertRaises(
            IntegrityError
        ):
            with transaction.atomic():
                BoardTaskDependency.objects.create(
                    task=task,
                    depends_on=dependency,
                )

    def test_self_dependency_is_rejected_by_database(
        self,
    ):
        task = self.create_task()

        with self.assertRaises(
            IntegrityError
        ):
            with transaction.atomic():
                BoardTaskDependency.objects.create(
                    task=task,
                    depends_on=task,
                )

    def test_model_ordering_uses_sort_order_then_created_at(
        self,
    ):
        second = self.create_task(
            title="Second",
            sort_order=2,
        )

        first = self.create_task(
            title="First",
            sort_order=1,
        )

        tasks = list(
            BoardTask.objects.filter(
                id__in=[
                    first.id,
                    second.id,
                ]
            )
        )

        self.assertEqual(
            tasks,
            [
                first,
                second,
            ],
        )


class BoardTaskAuthenticationTests(
    BoardTestBase
):
    def test_anonymous_user_cannot_list_tasks(
        self,
    ):
        self.client.force_authenticate(
            user=None,
        )

        response = self.client.get(
            self.list_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_anonymous_user_cannot_create_task(
        self,
    ):
        self.client.force_authenticate(
            user=None,
        )

        response = self.client.post(
            self.list_url,
            {
                "goal": self.goal.id,
                "title": "Unauthorised task",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class BoardTaskListTests(
    BoardTestBase
):
    def test_user_only_sees_own_tasks(
        self,
    ):
        own_task = self.create_task(
            title="Own task",
        )

        self.create_task(
            goal=self.other_goal,
            title="Other task",
        )

        response = self.client.get(
            self.list_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            item["id"]
            for item in response.data
        }

        self.assertEqual(
            returned_ids,
            {
                own_task.id,
            },
        )

    def test_list_can_be_filtered_by_goal(
        self,
    ):
        first_task = self.create_task(
            goal=self.goal,
            title="IELTS task",
        )

        self.create_task(
            goal=self.second_goal,
            title="PROJECT task",
        )

        response = self.client.get(
            self.list_url,
            {
                "goal": self.goal.id,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            [
                item["id"]
                for item in response.data
            ],
            [
                first_task.id,
            ],
        )

    def test_list_can_be_filtered_by_status(
        self,
    ):
        todo_task = self.create_task(
            title="Todo task",
            task_status=BoardTask.TODO,
        )

        self.create_task(
            title="Done task",
            task_status=BoardTask.DONE,
        )

        response = self.client.get(
            self.list_url,
            {
                "status": BoardTask.TODO,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            [
                item["id"]
                for item in response.data
            ],
            [
                todo_task.id,
            ],
        )

    def test_invalid_goal_filter_returns_400(
        self,
    ):
        response = self.client.get(
            self.list_url,
            {
                "goal": "not-an-id",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_status_filter_returns_400(
        self,
    ):
        response = self.client.get(
            self.list_url,
            {
                "status": "unknown",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )


class BoardTaskCreateTests(
    BoardTestBase
):
    def test_user_can_create_full_task(
        self,
    ):
        due_date = (
            timezone.localdate()
            + timedelta(days=7)
        )

        response = self.client.post(
            self.list_url,
            {
                "goal": self.goal.id,
                "title": "  Book IELTS exam  ",
                "description": (
                    "  Choose a date and centre.  "
                ),
                "status": BoardTask.TODO,
                "priority": BoardTask.PRIORITY_HIGH,
                "importance": (
                    BoardTask.IMPORTANCE_LARGE
                ),
                "due_date": str(due_date),
                "position_x": 2400,
                "position_y": 3600,
                "sort_order": 2,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        task = BoardTask.objects.get(
            id=response.data["id"],
        )

        self.assertEqual(
            task.goal,
            self.goal,
        )

        self.assertEqual(
            task.title,
            "Book IELTS exam",
        )

        self.assertEqual(
            task.description,
            "Choose a date and centre.",
        )

        self.assertEqual(
            task.priority,
            BoardTask.PRIORITY_HIGH,
        )

        self.assertEqual(
            task.importance,
            BoardTask.IMPORTANCE_LARGE,
        )

        self.assertEqual(
            task.due_date,
            due_date,
        )

        self.assertEqual(
            task.position_x,
            2400,
        )

        self.assertEqual(
            task.position_y,
            3600,
        )

        self.assertEqual(
            task.sort_order,
            2,
        )

        self.assertEqual(
            task.source,
            BoardTask.SOURCE_MANUAL,
        )

    def test_create_rejects_blank_title(
        self,
    ):
        response = self.client.post(
            self.list_url,
            {
                "goal": self.goal.id,
                "title": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            BoardTask.objects.exists()
        )

    def test_user_cannot_create_task_for_another_users_goal(
        self,
    ):
        response = self.client.post(
            self.list_url,
            {
                "goal": self.other_goal.id,
                "title": "Forbidden task",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            BoardTask.objects.filter(
                title="Forbidden task",
            ).exists()
        )

    def test_client_cannot_override_task_source(
        self,
    ):
        response = self.client.post(
            self.list_url,
            {
                "goal": self.goal.id,
                "title": "Manual task",
                "source": (
                    BoardTask.SOURCE_GOAL_AI
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        task = BoardTask.objects.get(
            id=response.data["id"],
        )

        self.assertEqual(
            task.source,
            BoardTask.SOURCE_MANUAL,
        )

    def test_create_done_task_sets_completed_at(
        self,
    ):
        response = self.client.post(
            self.list_url,
            {
                "goal": self.goal.id,
                "title": "Already completed task",
                "status": BoardTask.DONE,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        task = BoardTask.objects.get(
            id=response.data["id"],
        )

        self.assertIsNotNone(
            task.completed_at,
        )

    def test_create_task_with_dependency(
        self,
    ):
        dependency = self.create_task(
            title="Choose test centre",
        )

        response = self.client.post(
            self.list_url,
            {
                "goal": self.goal.id,
                "title": "Book exam",
                "dependency_ids": [
                    dependency.id,
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        task = BoardTask.objects.get(
            id=response.data["id"],
        )

        self.assertEqual(
            list(
                task.dependencies.all()
            ),
            [
                dependency,
            ],
        )

        self.assertTrue(
            response.data["is_blocked"]
        )

        self.assertEqual(
            response.data[
                "blocking_tasks"
            ][0]["id"],
            dependency.id,
        )

    def test_create_rejects_dependency_owned_by_another_user(
        self,
    ):
        foreign_dependency = self.create_task(
            goal=self.other_goal,
            title="Foreign dependency",
        )

        response = self.client.post(
            self.list_url,
            {
                "goal": self.goal.id,
                "title": "My task",
                "dependency_ids": [
                    foreign_dependency.id,
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_create_rejects_in_progress_task_with_unfinished_dependency(
        self,
    ):
        dependency = self.create_task(
            title="Blocking task",
        )

        response = self.client.post(
            self.list_url,
            {
                "goal": self.goal.id,
                "title": "Blocked task",
                "status": (
                    BoardTask.IN_PROGRESS
                ),
                "dependency_ids": [
                    dependency.id,
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "status",
            response.data,
        )

    def test_create_allows_in_progress_task_when_dependency_is_done(
        self,
    ):
        dependency = self.create_task(
            title="Completed dependency",
            task_status=BoardTask.DONE,
        )

        response = self.client.post(
            self.list_url,
            {
                "goal": self.goal.id,
                "title": "Available task",
                "status": (
                    BoardTask.IN_PROGRESS
                ),
                "dependency_ids": [
                    dependency.id,
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )


class BoardTaskDetailTests(
    BoardTestBase
):
    def test_user_can_retrieve_own_task(
        self,
    ):
        task = self.create_task()

        response = self.client.get(
            self.task_detail_url(task),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            task.id,
        )

    def test_user_cannot_retrieve_another_users_task(
        self,
    ):
        task = self.create_task(
            goal=self.other_goal,
        )

        response = self.client.get(
            self.task_detail_url(task),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_user_can_update_task_content(
        self,
    ):
        task = self.create_task()

        response = self.client.patch(
            self.task_detail_url(task),
            {
                "title": "  Updated task  ",
                "description": (
                    "  Updated description  "
                ),
                "priority": (
                    BoardTask.PRIORITY_CRITICAL
                ),
                "importance": (
                    BoardTask.IMPORTANCE_LARGE
                ),
                "due_date": "2026-09-15",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        task.refresh_from_db()

        self.assertEqual(
            task.title,
            "Updated task",
        )

        self.assertEqual(
            task.description,
            "Updated description",
        )

        self.assertEqual(
            task.priority,
            BoardTask.PRIORITY_CRITICAL,
        )

        self.assertEqual(
            task.importance,
            BoardTask.IMPORTANCE_LARGE,
        )

        self.assertEqual(
            task.due_date,
            date(
                2026,
                9,
                15,
            ),
        )

    def test_user_cannot_update_another_users_task(
        self,
    ):
        task = self.create_task(
            goal=self.other_goal,
        )

        response = self.client.patch(
            self.task_detail_url(task),
            {
                "title": "Changed",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_status_done_sets_completed_at(
        self,
    ):
        task = self.create_task()

        response = self.client.patch(
            self.task_detail_url(task),
            {
                "status": BoardTask.DONE,
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
            BoardTask.DONE,
        )

        self.assertIsNotNone(
            task.completed_at,
        )

    def test_reopening_task_clears_completed_at(
        self,
    ):
        task = self.create_task(
            task_status=BoardTask.DONE,
        )

        task.completed_at = timezone.now()

        task.save(
            update_fields=[
                "completed_at",
            ]
        )

        response = self.client.patch(
            self.task_detail_url(task),
            {
                "status": BoardTask.TODO,
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
            BoardTask.TODO,
        )

        self.assertIsNone(
            task.completed_at,
        )

    def test_blocked_task_cannot_start(
        self,
    ):
        dependency = self.create_task(
            title="Blocking task",
        )

        task = self.create_task(
            title="Blocked task",
        )

        BoardTaskDependency.objects.create(
            task=task,
            depends_on=dependency,
        )

        response = self.client.patch(
            self.task_detail_url(task),
            {
                "status": (
                    BoardTask.IN_PROGRESS
                ),
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

    def test_task_can_start_after_dependency_is_completed(
        self,
    ):
        dependency = self.create_task(
            title="Blocking task",
            task_status=BoardTask.DONE,
        )

        task = self.create_task(
            title="Available task",
        )

        BoardTaskDependency.objects.create(
            task=task,
            depends_on=dependency,
        )

        response = self.client.patch(
            self.task_detail_url(task),
            {
                "status": (
                    BoardTask.IN_PROGRESS
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_task_dependencies_can_be_replaced(
        self,
    ):
        first_dependency = self.create_task(
            title="First dependency",
        )

        second_dependency = self.create_task(
            title="Second dependency",
        )

        task = self.create_task(
            title="Dependent task",
        )

        BoardTaskDependency.objects.create(
            task=task,
            depends_on=first_dependency,
        )

        response = self.client.patch(
            self.task_detail_url(task),
            {
                "dependency_ids": [
                    second_dependency.id,
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            list(
                task.dependencies.all()
            ),
            [
                second_dependency,
            ],
        )

    def test_task_cannot_depend_on_itself(
        self,
    ):
        task = self.create_task()

        response = self.client.patch(
            self.task_detail_url(task),
            {
                "dependency_ids": [
                    task.id,
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_circular_dependency_is_rejected(
        self,
    ):
        first = self.create_task(
            title="First",
        )

        second = self.create_task(
            title="Second",
        )

        third = self.create_task(
            title="Third",
        )

        BoardTaskDependency.objects.create(
            task=second,
            depends_on=first,
        )

        BoardTaskDependency.objects.create(
            task=third,
            depends_on=second,
        )

        response = self.client.patch(
            self.task_detail_url(first),
            {
                "dependency_ids": [
                    third.id,
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_task_can_move_to_another_owned_goal(
        self,
    ):
        task = self.create_task(
            goal=self.goal,
        )

        response = self.client.patch(
            self.task_detail_url(task),
            {
                "goal": self.second_goal.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        task.refresh_from_db()

        self.assertEqual(
            task.goal,
            self.second_goal,
        )

    def test_task_cannot_move_to_another_users_goal(
        self,
    ):
        task = self.create_task()

        response = self.client.patch(
            self.task_detail_url(task),
            {
                "goal": self.other_goal.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        task.refresh_from_db()

        self.assertEqual(
            task.goal,
            self.goal,
        )


class BoardTaskDeleteTests(
    BoardTestBase
):
    def test_user_can_delete_own_task(
        self,
    ):
        task = self.create_task()

        response = self.client.delete(
            self.task_detail_url(task),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            BoardTask.objects.filter(
                id=task.id,
            ).exists()
        )

    def test_user_cannot_delete_another_users_task(
        self,
    ):
        task = self.create_task(
            goal=self.other_goal,
        )

        response = self.client.delete(
            self.task_detail_url(task),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertTrue(
            BoardTask.objects.filter(
                id=task.id,
            ).exists()
        )

    def test_delete_task_removes_dependency_links(
        self,
    ):
        dependency = self.create_task(
            title="Dependency",
        )

        task = self.create_task(
            title="Dependent task",
        )

        link = BoardTaskDependency.objects.create(
            task=task,
            depends_on=dependency,
        )

        response = self.client.delete(
            self.task_detail_url(
                dependency
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            BoardTaskDependency.objects.filter(
                id=link.id,
            ).exists()
        )


class BoardGoalProgressTests(
    BoardTestBase
):
    def test_creating_first_unfinished_task_keeps_progress_zero(
        self,
    ):
        response = self.client.post(
            self.list_url,
            {
                "goal": self.goal.id,
                "title": "First task",
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

    def test_completing_one_of_two_tasks_sets_progress_to_50(
        self,
    ):
        first = self.create_task(
            title="First",
        )

        self.create_task(
            title="Second",
        )

        response = self.client.patch(
            self.task_detail_url(first),
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

    def test_completing_all_tasks_completes_goal(
        self,
    ):
        task = self.create_task()

        response = self.client.patch(
            self.task_detail_url(task),
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

    def test_completing_goal_creates_one_win(
        self,
    ):
        task = self.create_task()

        self.client.patch(
            self.task_detail_url(task),
            {
                "status": BoardTask.DONE,
            },
            format="json",
        )

        wins = Win.objects.filter(
            user=self.user,
            source="goal",
            source_id=str(self.goal.id),
        )

        self.assertEqual(
            wins.count(),
            1,
        )

    def test_repeated_done_update_does_not_duplicate_win(
        self,
    ):
        task = self.create_task()

        detail_url = self.task_detail_url(
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
            source="goal",
            source_id=str(self.goal.id),
        )

        self.assertEqual(
            wins.count(),
            1,
        )

    def test_reopening_completed_task_reopens_goal(
        self,
    ):
        task = self.create_task(
            task_status=BoardTask.DONE,
        )

        task.completed_at = timezone.now()

        task.save(
            update_fields=[
                "completed_at",
            ]
        )

        self.goal.status = Goal.COMPLETED
        self.goal.progress = 100
        self.goal.completed_at = (
            timezone.now()
        )

        self.goal.save(
            update_fields=[
                "status",
                "progress",
                "completed_at",
                "updated_at",
            ]
        )

        response = self.client.patch(
            self.task_detail_url(task),
            {
                "status": BoardTask.TODO,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.goal.refresh_from_db()

        self.assertEqual(
            self.goal.status,
            Goal.ACTIVE,
        )

        self.assertEqual(
            self.goal.progress,
            0,
        )

        self.assertIsNone(
            self.goal.completed_at,
        )

    def test_deleting_task_recalculates_goal_progress(
        self,
    ):
        done_task = self.create_task(
            title="Done",
            task_status=BoardTask.DONE,
        )

        todo_task = self.create_task(
            title="Todo",
            task_status=BoardTask.TODO,
        )

        self.goal.progress = 50

        self.goal.save(
            update_fields=[
                "progress",
                "updated_at",
            ]
        )

        response = self.client.delete(
            self.task_detail_url(
                todo_task
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
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

        self.assertTrue(
            BoardTask.objects.filter(
                id=done_task.id,
            ).exists()
        )

    def test_moving_task_recalculates_both_goals(
        self,
    ):
        completed_task = self.create_task(
            goal=self.goal,
            title="Completed",
            task_status=BoardTask.DONE,
        )

        moving_task = self.create_task(
            goal=self.goal,
            title="Move me",
            task_status=BoardTask.TODO,
        )

        other_done_task = self.create_task(
            goal=self.second_goal,
            title="Already done",
            task_status=BoardTask.DONE,
        )

        self.goal.progress = 50
        self.second_goal.progress = 100

        self.goal.save(
            update_fields=[
                "progress",
                "updated_at",
            ]
        )

        self.second_goal.save(
            update_fields=[
                "progress",
                "updated_at",
            ]
        )

        response = self.client.patch(
            self.task_detail_url(
                moving_task
            ),
            {
                "goal": self.second_goal.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.goal.refresh_from_db()
        self.second_goal.refresh_from_db()

        self.assertEqual(
            self.goal.progress,
            100,
        )

        self.assertEqual(
            self.goal.status,
            Goal.COMPLETED,
        )

        self.assertEqual(
            self.second_goal.progress,
            50,
        )

        self.assertEqual(
            self.second_goal.status,
            Goal.ACTIVE,
        )

        self.assertTrue(
            BoardTask.objects.filter(
                id=completed_task.id,
            ).exists()
        )

        self.assertTrue(
            BoardTask.objects.filter(
                id=other_done_task.id,
            ).exists()
        )


class BoardTaskLayoutTests(
    BoardTestBase
):
    def test_layout_requires_task_list(
        self,
    ):
        response = self.client.patch(
            self.layout_url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_layout_rejects_empty_list(
        self,
    ):
        response = self.client.patch(
            self.layout_url,
            {
                "tasks": [],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_layout_updates_position_and_order(
        self,
    ):
        task = self.create_task()

        response = self.client.patch(
            self.layout_url,
            {
                "tasks": [
                    {
                        "id": task.id,
                        "position_x": 1800,
                        "position_y": 7200,
                        "sort_order": 4,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        task.refresh_from_db()

        self.assertEqual(
            task.position_x,
            1800,
        )

        self.assertEqual(
            task.position_y,
            7200,
        )

        self.assertEqual(
            task.sort_order,
            4,
        )

    def test_layout_can_change_status(
        self,
    ):
        task = self.create_task()

        response = self.client.patch(
            self.layout_url,
            {
                "tasks": [
                    {
                        "id": task.id,
                        "status": (
                            BoardTask.IN_PROGRESS
                        ),
                        "position_x": 3000,
                        "position_y": 4000,
                        "sort_order": 0,
                    }
                ],
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

    def test_layout_sets_completed_at_when_moved_to_done(
        self,
    ):
        task = self.create_task()

        response = self.client.patch(
            self.layout_url,
            {
                "tasks": [
                    {
                        "id": task.id,
                        "status": BoardTask.DONE,
                    }
                ],
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
            BoardTask.DONE,
        )

        self.assertIsNotNone(
            task.completed_at,
        )

    def test_layout_rejects_invalid_coordinates(
        self,
    ):
        task = self.create_task()

        response = self.client.patch(
            self.layout_url,
            {
                "tasks": [
                    {
                        "id": task.id,
                        "position_x": 10001,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        task.refresh_from_db()

        self.assertEqual(
            task.position_x,
            5000,
        )

    def test_layout_rejects_negative_sort_order(
        self,
    ):
        task = self.create_task()

        response = self.client.patch(
            self.layout_url,
            {
                "tasks": [
                    {
                        "id": task.id,
                        "sort_order": -1,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_layout_rejects_duplicate_task_ids(
        self,
    ):
        task = self.create_task()

        response = self.client.patch(
            self.layout_url,
            {
                "tasks": [
                    {
                        "id": task.id,
                        "position_x": 1000,
                    },
                    {
                        "id": task.id,
                        "position_x": 2000,
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_layout_rejects_other_users_task(
        self,
    ):
        task = self.create_task(
            goal=self.other_goal,
        )

        response = self.client.patch(
            self.layout_url,
            {
                "tasks": [
                    {
                        "id": task.id,
                        "position_x": 1000,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_layout_rejects_starting_blocked_task(
        self,
    ):
        dependency = self.create_task(
            title="Dependency",
        )

        task = self.create_task(
            title="Blocked",
        )

        BoardTaskDependency.objects.create(
            task=task,
            depends_on=dependency,
        )

        response = self.client.patch(
            self.layout_url,
            {
                "tasks": [
                    {
                        "id": task.id,
                        "status": (
                            BoardTask.IN_PROGRESS
                        ),
                    }
                ],
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

    def test_layout_allows_dependency_and_dependent_to_finish_together(
        self,
    ):
        dependency = self.create_task(
            title="Dependency",
        )

        dependent = self.create_task(
            title="Dependent",
        )

        BoardTaskDependency.objects.create(
            task=dependent,
            depends_on=dependency,
        )

        response = self.client.patch(
            self.layout_url,
            {
                "tasks": [
                    {
                        "id": dependency.id,
                        "status": BoardTask.DONE,
                    },
                    {
                        "id": dependent.id,
                        "status": BoardTask.DONE,
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        dependency.refresh_from_db()
        dependent.refresh_from_db()

        self.assertEqual(
            dependency.status,
            BoardTask.DONE,
        )

        self.assertEqual(
            dependent.status,
            BoardTask.DONE,
        )

    def test_layout_update_is_atomic(
        self,
    ):
        first = self.create_task(
            title="First",
        )

        second = self.create_task(
            title="Second",
        )

        response = self.client.patch(
            self.layout_url,
            {
                "tasks": [
                    {
                        "id": first.id,
                        "position_x": 1000,
                    },
                    {
                        "id": second.id,
                        "position_x": 15000,
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        first.refresh_from_db()
        second.refresh_from_db()

        self.assertEqual(
            first.position_x,
            5000,
        )

        self.assertEqual(
            second.position_x,
            5000,
        )


class BoardBrainSyncTests(
    BoardTestBase
):
    def test_create_task_updates_board_in_brain(
        self,
    ):
        response = self.client.post(
            self.list_url,
            {
                "goal": self.goal.id,
                "title": "Brain task",
                "priority": (
                    BoardTask.PRIORITY_HIGH
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.user.brain.refresh_from_db()

        board_progress = (
            self.user.brain.data[
                "progress"
            ][
                "board"
            ]
        )

        self.assertEqual(
            board_progress["total"],
            1,
        )

        self.assertEqual(
            board_progress["todo"],
            1,
        )

        board_tasks = (
            self.user.brain.data[
                "history"
            ][
                "board_tasks"
            ]
        )

        self.assertEqual(
            len(board_tasks),
            1,
        )

        self.assertEqual(
            board_tasks[0]["title"],
            "Brain task",
        )

    def test_brain_next_task_prefers_in_progress(
        self,
    ):
        self.create_task(
            title="High todo",
            task_status=BoardTask.TODO,
            priority=BoardTask.PRIORITY_CRITICAL,
        )

        in_progress = self.create_task(
            title="Current task",
            task_status=BoardTask.IN_PROGRESS,
            priority=BoardTask.PRIORITY_LOW,
        )

        response = self.client.patch(
            self.task_detail_url(
                in_progress
            ),
            {
                "description": "Trigger sync",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.brain.refresh_from_db()

        next_task = (
            self.user.brain.data[
                "context"
            ][
                "board"
            ][
                "next_task"
            ]
        )

        self.assertEqual(
            next_task["id"],
            in_progress.id,
        )

    def test_brain_next_task_excludes_blocked_tasks(
        self,
    ):
        dependency = self.create_task(
            title="Dependency",
        )

        blocked = self.create_task(
            title="Critical blocked task",
            priority=(
                BoardTask.PRIORITY_CRITICAL
            ),
        )

        available = self.create_task(
            title="Available task",
            priority=BoardTask.PRIORITY_LOW,
        )

        BoardTaskDependency.objects.create(
            task=blocked,
            depends_on=dependency,
        )

        response = self.client.patch(
            self.task_detail_url(
                available
            ),
            {
                "description": "Trigger sync",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.brain.refresh_from_db()

        board_context = (
            self.user.brain.data[
                "context"
            ][
                "board"
            ]
        )

        self.assertEqual(
            board_context[
                "next_task"
            ][
                "id"
            ],
            dependency.id,
        )

        blocked_ids = {
            task["id"]
            for task in board_context[
                "blocked_tasks"
            ]
        }

        self.assertIn(
            blocked.id,
            blocked_ids,
        )

    def test_delete_task_removes_it_from_brain(
        self,
    ):
        task = self.create_task(
            title="Temporary task",
        )

        trigger_response = self.client.patch(
            self.task_detail_url(task),
            {
                "description": "Sync first",
            },
            format="json",
        )

        self.assertEqual(
            trigger_response.status_code,
            status.HTTP_200_OK,
        )

        delete_response = self.client.delete(
            self.task_detail_url(task),
        )

        self.assertEqual(
            delete_response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.user.brain.refresh_from_db()

        board_tasks = (
            self.user.brain.data[
                "history"
            ][
                "board_tasks"
            ]
        )

        self.assertEqual(
            board_tasks,
            [],
        )

        board_progress = (
            self.user.brain.data[
                "progress"
            ][
                "board"
            ]
        )

        self.assertEqual(
            board_progress["total"],
            0,
        )