from brain.services import deep_merge_dict


def update_brain_from_win(win):
    brain = win.user.brain

    current_wins = brain.data.get("wins", [])

    current_wins.append(
        {
            "title": win.title,
            "size": win.size,
            "created_at": win.created_at.isoformat(),
        }
    )

    update_data = {
        "wins": current_wins
    }

    brain.data = deep_merge_dict(
        brain.data,
        update_data,
    )

    brain.save()