from brain.services import update_brain_data


def update_brain_from_daily_log(daily_log):
    update_data = {
        "context": {
            "last_daily_log": {
                "date": str(daily_log.date),
                "content": daily_log.content,
            }
        }
    }

    update_brain_data(
        user=daily_log.user,
        patch=update_data,
    )
