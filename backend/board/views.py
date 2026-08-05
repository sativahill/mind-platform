from __future__ import annotations

from typing import Any

from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from goals.models import Goal

from .models import BoardTask
from .serializers import BoardTaskSerializer
from .services import (
    bulk_update_task_layout,
    delete_board_task,
    finalize_created_task,
    finalize_updated_task,
)


def get_user_tasks_queryset(user):
    """
    Единый queryset Board-задач пользователя.

    Загружает Goal и зависимости заранее, чтобы serializer
    не создавал отдельные запросы для каждой задачи.
    """
    return (
        BoardTask.objects.filter(
            goal__user=user,
        )
        .select_related(
            "goal",
            "goal__user",
        )
        .prefetch_related(
            "dependencies",
            "dependent_tasks",
        )
        .order_by(
            "sort_order",
            "created_at",
        )
    )


class BoardTaskView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        """
        Возвращает все задачи текущего пользователя.

        Поддерживаемые фильтры:

        /api/board/?goal=4
        /api/board/?status=todo
        /api/board/?goal=4&status=in_progress
        """
        tasks = get_user_tasks_queryset(
            request.user
        )

        goal_id = request.query_params.get(
            "goal"
        )

        task_status = request.query_params.get(
            "status"
        )

        if goal_id:
            try:
                goal_id = int(goal_id)
            except (
                TypeError,
                ValueError,
            ):
                return Response(
                    {
                        "goal": [
                            "Goal must be a valid integer."
                        ]
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            tasks = tasks.filter(
                goal_id=goal_id,
            )

        if task_status:
            valid_statuses = {
                choice[0]
                for choice
                in BoardTask.STATUS_CHOICES
            }

            if (
                task_status
                not in valid_statuses
            ):
                return Response(
                    {
                        "status": [
                            "Invalid task status."
                        ]
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            tasks = tasks.filter(
                status=task_status,
            )

        serializer = BoardTaskSerializer(
            tasks,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def post(self, request):
        """
        Создаёт новую Board-задачу.

        После создания:

        - синхронизируется completed_at;
        - пересчитывается Goal;
        - completed Goal при необходимости возвращается в active;
        - обновляются Goals и Board в Brain.
        """
        serializer = BoardTaskSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        task = serializer.save(
            source=BoardTask.SOURCE_MANUAL,
        )

        task = finalize_created_task(
            task
        )

        response_task = (
            get_user_tasks_queryset(
                request.user
            ).get(
                id=task.id,
            )
        )

        response_serializer = (
            BoardTaskSerializer(
                response_task,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class BoardTaskDetailView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get_object(
        self,
        request,
        task_id,
    ):
        return get_object_or_404(
            get_user_tasks_queryset(
                request.user
            ),
            id=task_id,
        )

    def get(
        self,
        request,
        task_id,
    ):
        """
        Возвращает одну задачу пользователя.
        """
        task = self.get_object(
            request,
            task_id,
        )

        serializer = BoardTaskSerializer(
            task,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def patch(
        self,
        request,
        task_id,
    ):
        """
        Частично обновляет задачу.

        Поддерживает изменение:

        - goal;
        - title;
        - description;
        - status;
        - priority;
        - importance;
        - due_date;
        - position_x;
        - position_y;
        - sort_order;
        - dependency_ids.
        """
        task = get_object_or_404(
            BoardTask.objects
            .select_for_update()
            .select_related(
                "goal",
                "goal__user",
            )
            .prefetch_related(
                "dependencies",
            ),
            id=task_id,
            goal__user=request.user,
        )

        previous_goal = task.goal
        previous_status = task.status

        serializer = BoardTaskSerializer(
            task,
            data=request.data,
            partial=True,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        updated_task = serializer.save()

        updated_task = (
            finalize_updated_task(
                updated_task,
                previous_goal=previous_goal,
                previous_status=previous_status,
            )
        )

        response_task = (
            get_user_tasks_queryset(
                request.user
            ).get(
                id=updated_task.id,
            )
        )

        response_serializer = (
            BoardTaskSerializer(
                response_task,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def delete(
        self,
        request,
        task_id,
    ):
        """
        Удаляет задачу пользователя.

        После удаления:

        - удаляются dependency-связи через cascade;
        - пересчитывается Goal;
        - при необходимости Goal возвращается в active;
        - обновляется Brain.
        """
        task = get_object_or_404(
            BoardTask.objects
            .select_for_update()
            .select_related(
                "goal",
                "goal__user",
            ),
            id=task_id,
            goal__user=request.user,
        )

        delete_board_task(
            task
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class BoardTaskLayoutView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    @transaction.atomic
    def patch(self, request):
        """
        Атомарно сохраняет layout после drag-and-drop.

        Формат запроса:

        {
            "tasks": [
                {
                    "id": 4,
                    "status": "in_progress",
                    "position_x": 2800,
                    "position_y": 3600,
                    "sort_order": 0
                },
                {
                    "id": 8,
                    "status": "todo",
                    "position_x": 5200,
                    "position_y": 4700,
                    "sort_order": 1
                }
            ]
        }

        Можно передавать только изменившиеся поля, но у каждого
        элемента обязательно должен присутствовать id.
        """
        raw_updates = request.data.get(
            "tasks"
        )

        if not isinstance(
            raw_updates,
            list,
        ):
            return Response(
                {
                    "tasks": [
                        (
                            "This field must be "
                            "a list."
                        )
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not raw_updates:
            return Response(
                {
                    "tasks": [
                        (
                            "At least one task "
                            "is required."
                        )
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_updates, errors = (
            self._validate_updates(
                request=request,
                raw_updates=raw_updates,
            )
        )

        if errors:
            return Response(
                {
                    "tasks": errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            updated_tasks = (
                bulk_update_task_layout(
                    user=request.user,
                    task_updates=(
                        validated_updates
                    ),
                )
            )
        except ValueError as error:
            return Response(
                {
                    "tasks": [
                        str(error)
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = BoardTaskSerializer(
            updated_tasks,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def _validate_updates(
        self,
        *,
        request,
        raw_updates,
    ):
        errors: dict[str, Any] = {}
        normalized_updates = []
        task_ids = []

        allowed_fields = {
            "id",
            "status",
            "position_x",
            "position_y",
            "sort_order",
        }

        valid_statuses = {
            choice[0]
            for choice
            in BoardTask.STATUS_CHOICES
        }

        for index, raw_update in enumerate(
            raw_updates
        ):
            item_errors = {}

            if not isinstance(
                raw_update,
                dict,
            ):
                errors[str(index)] = [
                    (
                        "Each item must be "
                        "an object."
                    )
                ]
                continue

            unknown_fields = (
                set(raw_update.keys())
                - allowed_fields
            )

            if unknown_fields:
                item_errors[
                    "non_field_errors"
                ] = [
                    (
                        "Unsupported fields: "
                        + ", ".join(
                            sorted(
                                unknown_fields
                            )
                        )
                        + "."
                    )
                ]

            task_id = raw_update.get(
                "id"
            )

            try:
                task_id = int(task_id)
            except (
                TypeError,
                ValueError,
            ):
                item_errors["id"] = [
                    (
                        "A valid task id "
                        "is required."
                    )
                ]

            normalized_update = {}

            if "id" not in item_errors:
                normalized_update[
                    "id"
                ] = task_id

                task_ids.append(
                    task_id
                )

            if "status" in raw_update:
                task_status = (
                    raw_update["status"]
                )

                if (
                    task_status
                    not in valid_statuses
                ):
                    item_errors[
                        "status"
                    ] = [
                        (
                            "Invalid task "
                            "status."
                        )
                    ]
                else:
                    normalized_update[
                        "status"
                    ] = task_status

            for field in (
                "position_x",
                "position_y",
            ):
                if field not in raw_update:
                    continue

                try:
                    value = int(
                        raw_update[field]
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    item_errors[field] = [
                        (
                            "This value must "
                            "be an integer."
                        )
                    ]
                    continue

                if not 0 <= value <= 10000:
                    item_errors[field] = [
                        (
                            "This value must be "
                            "between 0 and 10000."
                        )
                    ]
                    continue

                normalized_update[
                    field
                ] = value

            if "sort_order" in raw_update:
                try:
                    sort_order = int(
                        raw_update[
                            "sort_order"
                        ]
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    item_errors[
                        "sort_order"
                    ] = [
                        (
                            "This value must "
                            "be an integer."
                        )
                    ]
                else:
                    if sort_order < 0:
                        item_errors[
                            "sort_order"
                        ] = [
                            (
                                "This value cannot "
                                "be negative."
                            )
                        ]
                    else:
                        normalized_update[
                            "sort_order"
                        ] = sort_order

            if len(
                normalized_update
            ) == 1:
                item_errors[
                    "non_field_errors"
                ] = [
                    (
                        "Provide at least one "
                        "field to update."
                    )
                ]

            if item_errors:
                errors[str(index)] = (
                    item_errors
                )
            else:
                normalized_updates.append(
                    normalized_update
                )

        if errors:
            return [], errors

        if (
            len(task_ids)
            != len(set(task_ids))
        ):
            return [], {
                "non_field_errors": [
                    (
                        "The same task cannot "
                        "appear more than once."
                    )
                ]
            }

        tasks = list(
            BoardTask.objects.filter(
                id__in=task_ids,
                goal__user=request.user,
            )
            .select_related(
                "goal",
            )
            .prefetch_related(
                "dependencies",
            )
        )

        if len(tasks) != len(task_ids):
            return [], {
                "non_field_errors": [
                    (
                        "One or more Board tasks "
                        "were not found."
                    )
                ]
            }

        tasks_by_id = {
            task.id: task
            for task in tasks
        }

        final_statuses = {
            task.id: task.status
            for task in tasks
        }

        for update in normalized_updates:
            if "status" in update:
                final_statuses[
                    update["id"]
                ] = update[
                    "status"
                ]

        external_dependency_ids = set()

        for task in tasks:
            external_dependency_ids.update(
                dependency.id
                for dependency
                in task.dependencies.all()
                if dependency.id
                not in final_statuses
            )

        external_statuses = {
            task.id: task.status
            for task in (
                BoardTask.objects.filter(
                    id__in=(
                        external_dependency_ids
                    ),
                    goal__user=request.user,
                )
            )
        }

        blocked_errors = {}

        for update in normalized_updates:
            task = tasks_by_id[
                update["id"]
            ]

            final_status = (
                final_statuses[
                    task.id
                ]
            )

            if final_status not in (
                BoardTask.IN_PROGRESS,
                BoardTask.DONE,
            ):
                continue

            unfinished_dependencies = []

            for dependency in (
                task.dependencies.all()
            ):
                dependency_status = (
                    final_statuses.get(
                        dependency.id,
                        external_statuses.get(
                            dependency.id,
                            dependency.status,
                        ),
                    )
                )

                if (
                    dependency_status
                    != BoardTask.DONE
                ):
                    unfinished_dependencies.append(
                        dependency.title
                    )

            if unfinished_dependencies:
                blocked_errors[
                    str(task.id)
                ] = [
                    (
                        "Complete the blocking "
                        "tasks first: "
                        + ", ".join(
                            unfinished_dependencies[
                                :3
                            ]
                        )
                        + (
                            ", …"
                            if len(
                                unfinished_dependencies
                            )
                            > 3
                            else ""
                        )
                        + "."
                    )
                ]

        if blocked_errors:
            return [], {
                "blocked": blocked_errors,
            }

        return (
            normalized_updates,
            {},
        )