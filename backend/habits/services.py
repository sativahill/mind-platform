from typing import Any

from django.db import transaction

from brain.services import update_brain_data
from wins.services import create_habit_streak_win

from .models import Habit


HABIT_STREAK_MILESTONES = {
    7,
    30,
    100,
}


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
    Rebuild the user's habits section from current database state.

    This is the single Habit -> Brain integration point and uses
    the same merge contract as the other integrated modules.

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

    """
    serialized_habits = serialize_user_habits_for_brain(
        user
    )

    update_brain_data(
        user=user,
        patch={
            "habits": serialized_habits,
        },
    )


@transaction.atomic
def finalize_habit_change(
    habit: Habit,
    *,
    refresh_streak: bool = False,
    check_streak_milestone: bool = False,
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

    if (
        check_streak_milestone
        and habit.streak
        in HABIT_STREAK_MILESTONES
    ):
        create_habit_streak_win(
            habit=habit,
            streak=habit.streak,
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
