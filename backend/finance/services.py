from brain.services import update_brain_data


def update_brain_from_finance_goal(goal):
    update_data = {
        "finance": {
            "last_goal": {
                "title": goal.title,
                "target_amount": str(goal.target_amount),
                "current_amount": str(goal.current_amount),
            }
        }
    }

    update_brain_data(
        user=goal.user,
        patch=update_data,
    )
