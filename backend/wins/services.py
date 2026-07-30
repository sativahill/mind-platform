from typing import Optional

from django.db import IntegrityError, transaction
from django.utils import timezone

from brain.services import deep_merge_dict

from .models import Win


def serialize_win_for_brain(win: Win) -> dict:
    """
    Представление победы, которое сохраняется внутри Brain.

    Не кладём туда технические поля вроде created_at,
    чтобы Brain оставался компактным и понятным для AI.
    """
    return {
        "id": win.id,
        "title": win.title,
        "description": win.description,
        "date": str(win.date),
        "size": win.size,
        "source": win.source,
        "source_id": win.source_id,
    }


def update_brain_from_win(win: Win) -> None:
    """
    Добавляет или обновляет победу в Brain.history.wins.

    Также сохраняет последнюю победу и общую статистику.
    Функция безопасна при повторном вызове для одного Win:
    существующая запись заменяется, а не дублируется.
    """
    brain = win.user.brain
    brain_data = brain.data or {}

    history = brain_data.setdefault(
        "history",
        {},
    )

    wins_history = history.setdefault(
        "wins",
        [],
    )

    serialized_win = serialize_win_for_brain(
        win
    )

    updated_wins = [
        stored_win
        for stored_win in wins_history
        if stored_win.get("id") != win.id
    ]

    updated_wins.append(
        serialized_win
    )

    updated_wins.sort(
        key=lambda stored_win: (
            stored_win.get(
                "date",
                "",
            ),
            stored_win.get(
                "id",
                0,
            ),
        ),
        reverse=True,
    )

    actual_last_win = (
        Win.objects
        .filter(user=win.user)
        .order_by(
            "-date",
            "-created_at",
        )
        .first()
    )

    serialized_last_win = (
        serialize_win_for_brain(
            actual_last_win
        )
        if actual_last_win
        else None
    )

    update_data = {
        "history": {
            "wins": updated_wins,
        },
        "context": {
            "last_win": serialized_last_win,
        },
        "progress": {
            "wins_count": (
                win.user.wins.count()
            ),
            "large_wins_count": (
                win.user.wins.filter(
                    size=Win.LARGE
                ).count()
            ),
        },
    }

    brain.data = deep_merge_dict(
        brain_data,
        update_data,
    )

    brain.save(
        update_fields=["data"]
    )


def sync_brain_wins(user) -> None:
    """
    Полностью пересобирает раздел wins внутри Brain.

    Используется после удаления победы или когда нужно
    гарантированно синхронизировать Brain с базой данных.
    """
    wins = list(
        Win.objects.filter(
            user=user
        )
    )

    serialized_wins = [
        serialize_win_for_brain(win)
        for win in wins
    ]

    last_win = (
        serialized_wins[0]
        if serialized_wins
        else None
    )

    brain = user.brain
    brain_data = brain.data or {}

    update_data = {
        "history": {
            "wins": serialized_wins,
        },
        "context": {
            "last_win": last_win,
        },
        "progress": {
            "wins_count": len(wins),
            "large_wins_count": sum(
                1
                for win in wins
                if win.size == Win.LARGE
            ),
        },
    }

    brain.data = deep_merge_dict(
        brain_data,
        update_data,
    )

    brain.save(
        update_fields=["data"]
    )


@transaction.atomic
def create_manual_win(
    *,
    user,
    title: str,
    size: str = Win.SMALL,
    description: str = "",
    date=None,
) -> Win:
    """
    Создаёт победу, которую пользователь добавил вручную.
    """
    win = Win.objects.create(
        user=user,
        title=title.strip(),
        description=description.strip(),
        date=date or timezone.localdate(),
        size=size,
        source=Win.MANUAL,
        source_id="",
        event_key=None,
    )

    update_brain_from_win(
        win
    )

    return win


@transaction.atomic
def create_automatic_win(
    *,
    user,
    title: str,
    source: str,
    event_key: str,
    source_id: str = "",
    size: str = Win.SMALL,
    description: str = "",
    date=None,
) -> tuple[Win, bool]:
    """
    Создаёт автоматическую победу из другого модуля.

    Возвращает:
        (win, created)

    created=False означает, что событие уже было обработано
    и повторная победа не была создана.
    """
    if source == Win.MANUAL:
        raise ValueError(
            "Automatic wins cannot use the manual source."
        )

    valid_sources = {
        choice[0]
        for choice in Win.SOURCE_CHOICES
    }

    if source not in valid_sources:
        raise ValueError(
            "Unknown win source."
        )

    normalized_event_key = event_key.strip()

    if not normalized_event_key:
        raise ValueError(
            "Automatic wins require an event_key."
        )

    try:
        with transaction.atomic():
            win, created = (
                Win.objects.get_or_create(
                    user=user,
                    event_key=(
                        normalized_event_key
                    ),
                    defaults={
                        "title": title.strip(),
                        "description": (
                            description.strip()
                        ),
                        "date": (
                            date
                            or timezone.localdate()
                        ),
                        "size": size,
                        "source": source,
                        "source_id": str(
                            source_id
                        ).strip(),
                    },
                )
            )
    except IntegrityError:
        win = Win.objects.get(
            user=user,
            event_key=normalized_event_key,
        )

        created = False

    if created:
        update_brain_from_win(
            win
        )

    return win, created


@transaction.atomic
def create_daily_log_win(
    *,
    daily_log,
    title: str,
    suggestion_key: str,
    suggestion_id: Optional[str] = None,
    size: str = Win.SMALL,
    description: str = "",
) -> tuple[Win, bool]:
    """
    Создаёт победу после подтверждения AI-предложения
    из конкретной записи Daily Log.

    suggestion_id используется только для поиска побед,
    созданных старой версией event_key. Новые победы всегда
    получают стабильный ключ DailyLogSuggestion.
    """
    if suggestion_id is not None:
        legacy_event_key = (
            f"daily_log:{daily_log.id}:"
            f"win:{suggestion_id}"
        )

        legacy_win = (
            Win.objects
            .filter(
                user=daily_log.user,
                source=Win.DAILY_LOG,
                source_id=str(
                    daily_log.id
                ),
                event_key=legacy_event_key,
            )
            .first()
        )

        if legacy_win is not None:
            return legacy_win, False

    return create_automatic_win(
        user=daily_log.user,
        title=title,
        description=description,
        date=daily_log.date,
        size=size,
        source=Win.DAILY_LOG,
        source_id=str(daily_log.id),
        event_key=(
            f"daily_log:{daily_log.id}:"
            f"win:{suggestion_key}"
        ),
    )


@transaction.atomic
def create_goal_win(
    *,
    goal,
    size: str = Win.LARGE,
    description: str = "",
) -> tuple[Win, bool]:
    """
    Создаёт победу после завершения цели.
    """
    return create_automatic_win(
        user=goal.user,
        title=f"Completed goal: {goal.title}",
        description=description,
        date=timezone.localdate(),
        size=size,
        source=Win.GOAL,
        source_id=str(goal.id),
        event_key=f"goal_completed:{goal.id}",
    )


@transaction.atomic
def create_habit_streak_win(
    *,
    habit,
    streak: int,
    size: Optional[str] = None,
) -> tuple[Win, bool]:
    """
    Создаёт победу за важную серию привычки.

    Размер автоматически зависит от длины серии:
    7 дней   → small
    30 дней  → medium
    100 дней → large
    """
    if streak <= 0:
        raise ValueError(
            "Streak must be greater than zero."
        )

    if size is None:
        if streak >= 100:
            size = Win.LARGE
        elif streak >= 30:
            size = Win.MEDIUM
        else:
            size = Win.SMALL

    return create_automatic_win(
        user=habit.user,
        title=(
            f"{streak}-day streak: "
            f"{habit.title}"
        ),
        size=size,
        source=Win.HABIT,
        source_id=str(habit.id),
        event_key=(
            f"habit_streak:{habit.id}:"
            f"{streak}"
        ),
    )
