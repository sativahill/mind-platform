from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone

from brain.services import update_brain_data
from goals.models import Goal
from goals.services import (
    recalculate_goal_progress,
    sync_brain_goals,
)

from .models import BoardTask


def serialize_task_for_brain(
    task: BoardTask,
) -> dict[str, Any]:
    """
    Компактное представление Board-задачи для Brain.

    В Brain сохраняются данные, которые полезны для AI,
    аналитики и понимания текущего контекста пользователя.
    """
    dependencies = list(
        task.dependencies.all()
    )

    blocking_tasks = [
        dependency
        for dependency in dependencies
        if dependency.status != BoardTask.DONE
    ]

    return {
        "id": task.id,
        "goal_id": task.goal_id,
        "goal_title": task.goal.title,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "importance": task.importance,
        "source": task.source,
        "due_date": (
            str(task.due_date)
            if task.due_date
            else None
        ),
        "completed_at": (
            task.completed_at.isoformat()
            if task.completed_at
            else None
        ),
        "position": {
            "x": task.position_x,
            "y": task.position_y,
        },
        "sort_order": task.sort_order,
        "dependency_ids": [
            dependency.id
            for dependency in dependencies
        ],
        "blocking_task_ids": [
            dependency.id
            for dependency in blocking_tasks
        ],
        "is_blocked": bool(
            blocking_tasks
        ),
    }


def sync_brain_board(
    user,
) -> None:
    """
    Полностью пересобирает Board-раздел Brain.

    Повторный вызов безопасен: данные заменяются актуальным
    состоянием Board, а не добавляются повторно.
    """
    tasks = list(
        BoardTask.objects.filter(
            goal__user=user,
        )
        .select_related(
            "goal",
        )
        .prefetch_related(
            Prefetch(
                "dependencies",
                queryset=(
                    BoardTask.objects
                    .select_related("goal")
                    .order_by(
                        "sort_order",
                        "created_at",
                    )
                ),
            )
        )
        .order_by(
            "sort_order",
            "created_at",
        )
    )

    serialized_tasks = [
        serialize_task_for_brain(
            task
        )
        for task in tasks
    ]

    todo_tasks = [
        task_data
        for task_data in serialized_tasks
        if task_data["status"]
        == BoardTask.TODO
    ]

    in_progress_tasks = [
        task_data
        for task_data in serialized_tasks
        if task_data["status"]
        == BoardTask.IN_PROGRESS
    ]

    done_tasks = [
        task_data
        for task_data in serialized_tasks
        if task_data["status"]
        == BoardTask.DONE
    ]

    blocked_tasks = [
        task_data
        for task_data in serialized_tasks
        if task_data["is_blocked"]
    ]

    overdue_tasks = [
        task_data
        for task_data in serialized_tasks
        if (
            task_data["due_date"]
            and task_data["status"]
            != BoardTask.DONE
            and task_data["due_date"]
            < str(timezone.localdate())
        )
    ]

    next_task = _select_next_task(
        serialized_tasks
    )

    update_data = {
        "progress": {
            "board": {
                "total": len(
                    serialized_tasks
                ),
                "todo": len(
                    todo_tasks
                ),
                "in_progress": len(
                    in_progress_tasks
                ),
                "done": len(
                    done_tasks
                ),
                "blocked": len(
                    blocked_tasks
                ),
                "overdue": len(
                    overdue_tasks
                ),
            },
        },
        "context": {
            "board": {
                "next_task": next_task,
                "in_progress_tasks": (
                    in_progress_tasks
                ),
                "overdue_tasks": (
                    overdue_tasks
                ),
                "blocked_tasks": (
                    blocked_tasks
                ),
            },
        },
        "history": {
            "board_tasks": (
                serialized_tasks
            ),
        },
    }

    update_brain_data(
        user=user,
        patch=update_data,
    )


def _select_next_task(
    tasks: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Выбирает следующую доступную задачу для Brain.

    Приоритет выбора:
    1. незаблокированная in_progress;
    2. незаблокированная todo;
    3. более высокий priority;
    4. ближайший due_date;
    5. sort_order.
    """
    available_tasks = [
        task
        for task in tasks
        if (
            task["status"]
            != BoardTask.DONE
            and not task["is_blocked"]
        )
    ]

    if not available_tasks:
        return None

    priority_order = {
        BoardTask.PRIORITY_CRITICAL: 0,
        BoardTask.PRIORITY_HIGH: 1,
        BoardTask.PRIORITY_MEDIUM: 2,
        BoardTask.PRIORITY_LOW: 3,
    }

    status_order = {
        BoardTask.IN_PROGRESS: 0,
        BoardTask.TODO: 1,
    }

    def sort_key(
        task: dict[str, Any],
    ):
        return (
            status_order.get(
                task["status"],
                2,
            ),
            priority_order.get(
                task["priority"],
                4,
            ),
            task["due_date"] is None,
            task["due_date"] or "",
            task["sort_order"],
            task["id"],
        )

    return min(
        available_tasks,
        key=sort_key,
    )


def _unique_goals(
    goals: Iterable[
        Goal | None
    ],
) -> list[Goal]:
    """
    Убирает None и повторяющиеся Goal.
    """
    unique: dict[int, Goal] = {}

    for goal in goals:
        if (
            goal is None
            or goal.pk is None
        ):
            continue

        unique[goal.pk] = goal

    return list(
        unique.values()
    )


def _get_goal_task_state(
    goal: Goal,
) -> tuple[int, int, int]:
    """
    Возвращает:
        total_tasks,
        done_tasks,
        calculated_progress
    """
    total_tasks = (
        goal.tasks.count()
    )

    if total_tasks == 0:
        return 0, 0, 0

    done_tasks = (
        goal.tasks.filter(
            status=BoardTask.DONE,
        ).count()
    )

    calculated_progress = int(
        done_tasks
        / total_tasks
        * 100
    )

    return (
        total_tasks,
        done_tasks,
        calculated_progress,
    )


@transaction.atomic
def reopen_goal_if_needed(
    goal: Goal,
) -> Goal:
    """
    Возвращает completed Goal в active, если её Board
    больше не соответствует завершённому состоянию.

    Это происходит, если:
    - выполненную задачу вернули в работу;
    - задачу удалили;
    - задачу перенесли в другую Goal;
    - у завершённой Goal появилась новая незавершённая задача.

    Созданный ранее Win не удаляется: он остаётся частью истории.
    Повторный Win не появится благодаря стабильному event_key.
    """
    if goal.status != Goal.COMPLETED:
        return goal

    (
        total_tasks,
        _done_tasks,
        calculated_progress,
    ) = _get_goal_task_state(
        goal
    )

    still_completed = (
        total_tasks > 0
        and calculated_progress == 100
    )

    if still_completed:
        return goal

    goal.status = Goal.ACTIVE
    goal.progress = (
        calculated_progress
    )
    goal.completed_at = None

    goal.save(
        update_fields=[
            "status",
            "progress",
            "completed_at",
            "updated_at",
        ]
    )

    return goal


@transaction.atomic
def reconcile_goal_from_board(
    goal: Goal,
) -> Goal:
    """
    Приводит Goal в соответствие с её задачами.

    Архивные цели не меняются автоматически.
    Completed Goal сначала при необходимости открывается,
    затем используется единый Goals-сервис пересчёта.
    """
    goal.refresh_from_db()

    if goal.status == Goal.ARCHIVED:
        return goal

    reopen_goal_if_needed(
        goal
    )

    goal.refresh_from_db()

    recalculated_goal = (
        recalculate_goal_progress(
            goal
        )
    )

    return recalculated_goal


@transaction.atomic
def reconcile_goals_from_board(
    *goals: Goal | None,
) -> None:
    """
    Пересчитывает все затронутые Goal без повторов.
    """
    unique_goals = _unique_goals(
        goals
    )

    affected_users = {}

    for goal in unique_goals:
        reconcile_goal_from_board(
            goal
        )

        affected_users[
            goal.user_id
        ] = goal.user

    for user in affected_users.values():
        sync_brain_goals(
            user
        )


def apply_task_completion_state(
    task: BoardTask,
) -> list[str]:
    """
    Синхронизирует completed_at со статусом задачи.

    Возвращает список полей, которые были изменены.
    """
    changed_fields = []

    if (
        task.status == BoardTask.DONE
        and task.completed_at is None
    ):
        task.completed_at = (
            timezone.now()
        )

        changed_fields.append(
            "completed_at"
        )

    if (
        task.status != BoardTask.DONE
        and task.completed_at
        is not None
    ):
        task.completed_at = None

        changed_fields.append(
            "completed_at"
        )

    return changed_fields


@transaction.atomic
def finalize_created_task(
    task: BoardTask,
) -> BoardTask:
    """
    Завершает бизнес-логику после создания задачи.

    - выставляет completed_at;
    - пересчитывает Goal;
    - обновляет Board в Brain.
    """
    changed_fields = (
        apply_task_completion_state(
            task
        )
    )

    if changed_fields:
        changed_fields.append(
            "updated_at"
        )

        task.save(
            update_fields=changed_fields,
        )

    reconcile_goals_from_board(
        task.goal
    )

    sync_brain_board(
        task.goal.user
    )

    task.refresh_from_db()

    return task


@transaction.atomic
def finalize_updated_task(
    task: BoardTask,
    *,
    previous_goal: Goal,
    previous_status: str,
) -> BoardTask:
    """
    Завершает бизнес-логику после изменения задачи.

    Обрабатывает:
    - смену статуса;
    - completed_at;
    - перенос между Goal;
    - пересчёт старой Goal;
    - пересчёт новой Goal;
    - обновление Board в Brain.
    """
    changed_fields = (
        apply_task_completion_state(
            task
        )
    )

    if changed_fields:
        changed_fields.append(
            "updated_at"
        )

        task.save(
            update_fields=changed_fields,
        )

    goal_changed = (
        previous_goal.id
        != task.goal_id
    )

    status_changed = (
        previous_status
        != task.status
    )

    if (
        goal_changed
        or status_changed
    ):
        reconcile_goals_from_board(
            previous_goal,
            task.goal,
        )

    else:
        sync_brain_goals(
            task.goal.user
        )

    sync_brain_board(
        task.goal.user
    )

    if (
        goal_changed
        and previous_goal.user_id
        != task.goal.user_id
    ):
        sync_brain_board(
            previous_goal.user
        )

    task.refresh_from_db()

    return task


@transaction.atomic
def delete_board_task(
    task: BoardTask,
) -> None:
    """
    Удаляет задачу и синхронизирует связанные модули.

    После удаления:
    - пересчитывается Goal;
    - completed Goal при необходимости возвращается в active;
    - Board и Goals обновляются в Brain.
    """
    goal = task.goal
    user = goal.user

    task.delete()

    reconcile_goals_from_board(
        goal
    )

    sync_brain_board(
        user
    )


@transaction.atomic
def update_task_position(
    *,
    task: BoardTask,
    position_x: int,
    position_y: int,
    sort_order: int | None = None,
) -> BoardTask:
    """
    Обновляет пространственную позицию стикера.

    Координаты нормализованы в диапазоне 0–10000,
    поэтому не зависят от фактических browser pixels.
    """
    task.position_x = position_x
    task.position_y = position_y

    update_fields = [
        "position_x",
        "position_y",
        "updated_at",
    ]

    if sort_order is not None:
        task.sort_order = sort_order

        update_fields.append(
            "sort_order"
        )

    task.save(
        update_fields=update_fields,
    )

    sync_brain_board(
        task.goal.user
    )

    return task


@transaction.atomic
def bulk_update_task_layout(
    *,
    user,
    task_updates: list[
        dict[str, int | str]
    ],
) -> list[BoardTask]:
    """
    Атомарно сохраняет drag-and-drop layout нескольких задач.

    Поддерживаемые значения для каждой задачи:
    - id;
    - status;
    - position_x;
    - position_y;
    - sort_order.

    Проверка диапазонов и допустимых статусов также останется
    на уровне API serializer/view.
    """
    task_ids = [
        int(update["id"])
        for update in task_updates
    ]

    tasks = {
        task.id: task
        for task in (
            BoardTask.objects
            .select_for_update()
            .select_related(
                "goal",
                "goal__user",
            )
            .filter(
                id__in=task_ids,
                goal__user=user,
            )
        )
    }

    if len(tasks) != len(
        set(task_ids)
    ):
        raise ValueError(
            "One or more Board tasks were not found."
        )

    previous_states = {
        task.id: {
            "goal": task.goal,
            "status": task.status,
        }
        for task in tasks.values()
    }

    affected_goals = []

    for update in task_updates:
        task = tasks[
            int(update["id"])
        ]

        if "status" in update:
            task.status = str(
                update["status"]
            )

        if "position_x" in update:
            task.position_x = int(
                update["position_x"]
            )

        if "position_y" in update:
            task.position_y = int(
                update["position_y"]
            )

        if "sort_order" in update:
            task.sort_order = int(
                update["sort_order"]
            )

        apply_task_completion_state(
            task
        )

        affected_goals.append(
            task.goal
        )

    BoardTask.objects.bulk_update(
        list(tasks.values()),
        [
            "status",
            "position_x",
            "position_y",
            "sort_order",
            "completed_at",
            "updated_at",
        ],
    )

    for task in tasks.values():
        previous_state = (
            previous_states[
                task.id
            ]
        )

        if (
            previous_state["status"]
            != task.status
        ):
            affected_goals.append(
                previous_state[
                    "goal"
                ]
            )

    reconcile_goals_from_board(
        *affected_goals
    )

    sync_brain_board(
        user
    )

    return list(
        BoardTask.objects
        .filter(
            id__in=task_ids,
            goal__user=user,
        )
        .select_related(
            "goal",
        )
        .prefetch_related(
            "dependencies",
        )
        .order_by(
            "sort_order",
            "created_at",
        )
    )
