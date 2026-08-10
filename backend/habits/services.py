from typing import Any

from django.db import transaction

from .models import Habit


def serialize_habit_for_brain(
    habit: Habit,
) -> dict[str, Any]:
    """
    Compact Habit representation for Brain/context sync.

    Keep this structure stable so Brain integration does not need
    to understand internal Habit model details.
    """
    return {
        "id": habit.id,
        "title": habit.title,
        "trigger": habit.trigger,
        "action": habit.action,
        "reward": habit.reward,
        "status": habit.status,
        "streak": habit.streak,
        "today_status": habit.today_status,
        "consecutive_misses": (
            habit.consecutive_misses()
        ),
    }


def serialize_user_habits_for_brain(
    user,
) -> list[dict[str, Any]]:
    """
    Return active habits in a compact Brain-friendly format.
    """
    habits = (
        Habit.objects
        .filter(
            user=user,
            status=Habit.Status.ACTIVE,
        )
        .prefetch_related(
            "completions",
        )
        .order_by(
            "-streak",
            "-updated_at",
        )
    )

    return [
        serialize_habit_for_brain(
            habit
        )
        for habit in habits
    ]


def refresh_habit_state(
    habit: Habit,
) -> Habit:
    """
    Recalculate derived Habit state.

    At the moment streak is the main persisted derived value.
    """
    habit.refresh_streak()

    return habit


def sync_brain_habits(
    user,
) -> None:
    """
    Brain integration boundary.

    Do not implement a second Brain storage mechanism here.

    This function is intentionally the single integration point
    for Habit -> Brain synchronization. Connect it to the existing
    Brain service used by Daily Log / Goals / Board once that
    service is imported here.

    Example shape that should be sent to Brain:

        {
            "habits": [
                {
                    "id": 1,
                    "title": "...",
                    "trigger": "...",
                    "action": "...",
                    "reward": "...",
                    "status": "active",
                    "streak": 5,
                    "today_status": "completed",
                    "consecutive_misses": 0,
                }
            ]
        }

    Do not create or update Brain models directly from this module
    until the project's existing Brain service contract is used.
    """
    _ = serialize_user_habits_for_brain(
        user
    )


@transaction.atomic
def finalize_habit_change(
    habit: Habit,
    *,
    refresh_streak: bool = False,
) -> Habit:
    """
    Finalize any Habit mutation.

    Use after create/update/archive/restore or a daily status change.
    """
    if refresh_streak:
        refresh_habit_state(
            habit
        )

    sync_brain_habits(
        habit.user
    )

    return habit


@transaction.atomic
def finalize_habit_delete(
    user,
) -> None:
    """
    Re-sync Habit context after deletion.
    """
    sync_brain_habits(
        user
    )