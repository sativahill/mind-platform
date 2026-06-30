from brain.services import deep_merge_dict


def update_brain_from_finance_goal(goal):
    brain = goal.user.brain

    update_data = {
        "finance": {
            "last_goal": {
                "title": goal.title,
                "target_amount": str(goal.target_amount),
                "current_amount": str(goal.current_amount),
            }
        }
    }

    brain.data = deep_merge_dict(
        brain.data,
        update_data,
    )

    brain.save()
