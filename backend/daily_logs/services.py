from brain.models import Brain

from brain.services import deep_merge_dict

def update_brain_from_daily_log(daily_log):
    brain = daily_log.user.brain

    update_data = {
        "context": {
            "last_daily_log": {
                "date": str(daily_log.date),
                "content": daily_log.content,
            }
        }
    }

    brain.data = deep_merge_dict(
        brain.data,
        update_data,
    )

    brain.save()