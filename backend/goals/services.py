from django.db import transaction
from django.utils import timezone

from brain.services import deep_merge_dict
from wins.services import create_goal_win

from .models import Goal


def serialize_goal_for_brain(goal: Goal) -> dict:
    """
    Возвращает компактное представление цели для Brain.

    В Brain сохраняются только данные, полезные для контекста AI.
    """
    return {
        "id": goal.id,
        "title": goal.title,
        "description": goal.description,
        "why_it_matters": goal.why_it_matters,
        "previous_obstacles": goal.previous_obstacles,
        "target_date": (
            str(goal.target_date)
            if goal.target_date
            else None
        ),
        "status": goal.status,
        "progress": goal.progress,
        "completed_at": (
            goal.completed_at.isoformat()
            if goal.completed_at
            else None
        ),
    }


def sync_brain_goals(user) -> None:
    """
    Полностью пересобирает информацию о целях пользователя
    внутри Brain.

    Повторный вызов безопасен: данные заменяются актуальным
    состоянием из базы, а не добавляются повторно.
    """
    goals = list(
        Goal.objects.filter(
            user=user,
        ).order_by(
            "-updated_at",
        )
    )

    serialized_goals = [
        serialize_goal_for_brain(goal)
        for goal in goals
    ]

    active_goals = [
        goal_data
        for goal_data in serialized_goals
        if goal_data["status"] == Goal.ACTIVE
    ]

    completed_goals = [
        goal_data
        for goal_data in serialized_goals
        if goal_data["status"] == Goal.COMPLETED
    ]

    archived_goals = [
        goal_data
        for goal_data in serialized_goals
        if goal_data["status"] == Goal.ARCHIVED
    ]

    primary_goal = (
        active_goals[0]
        if active_goals
        else None
    )

    brain = user.brain
    brain_data = brain.data or {}

    update_data = {
        "progress": {
            "goals": {
                "active": active_goals,
                "completed": completed_goals,
                "archived": archived_goals,
                "total_active": len(active_goals),
                "total_completed": len(completed_goals),
                "total_archived": len(archived_goals),
            },
        },
        "context": {
            "primary_goal": primary_goal,
        },
    }

    brain.data = deep_merge_dict(
        brain_data,
        update_data,
    )

    brain.save(
        update_fields=["data"],
    )


def update_brain_from_goal(goal: Goal) -> None:
    """
    Синхронизирует Goals-раздел Brain после изменения цели.
    """
    sync_brain_goals(
        goal.user,
    )


@transaction.atomic
def complete_goal(goal: Goal) -> Goal:
    """
    Завершает цель, фиксирует дату завершения,
    создаёт автоматическую победу и обновляет Brain.

    Повторный вызов безопасен: Win защищён event_key,
    а завершённые поля записываются только при необходимости.
    """
    if goal.status == Goal.ARCHIVED:
        return goal

    fields_to_update = []

    if goal.progress != 100:
        goal.progress = 100

    if goal.status != Goal.COMPLETED:
        goal.status = Goal.COMPLETED
        fields_to_update.append(
            "status"
        )

    if goal.completed_at is None:
        goal.completed_at = timezone.now()
        fields_to_update.append(
            "completed_at"
        )

    stored_progress = (
        Goal.objects.filter(
            pk=goal.pk,
        )
        .values_list(
            "progress",
            flat=True,
        )
        .first()
    )

    if stored_progress != 100:
        fields_to_update.append(
            "progress"
        )

    if fields_to_update:
        fields_to_update.append(
            "updated_at"
        )

        goal.save(
            update_fields=fields_to_update,
        )

    create_goal_win(
        goal=goal,
        description=(
            goal.why_it_matters
            or goal.description
        ),
    )

    update_brain_from_goal(
        goal,
    )

    return goal


@transaction.atomic
def recalculate_goal_progress(goal: Goal) -> Goal:
    """
    Пересчитывает прогресс цели по связанным задачам Board.

    Если все задачи выполнены, цель автоматически завершается.
    Архивные и уже завершённые цели не возвращаются
    автоматически в активное состояние.
    """
    if goal.status == Goal.ARCHIVED:
        return goal

    total_tasks = goal.tasks.count()

    if total_tasks == 0:
        calculated_progress = 0
    else:
        done_tasks = goal.tasks.filter(
            status="done",
        ).count()

        calculated_progress = int(
            done_tasks
            / total_tasks
            * 100
        )

    if calculated_progress == 100:
        return complete_goal(
            goal,
        )

    if goal.status == Goal.COMPLETED:
        return goal

    if goal.progress != calculated_progress:
        goal.progress = calculated_progress

        goal.save(
            update_fields=[
                "progress",
                "updated_at",
            ],
        )

    update_brain_from_goal(
        goal,
    )

    return goal