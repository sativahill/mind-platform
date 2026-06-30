from brain.services import deep_merge_dict


def update_brain_from_progress_photo(progress_photo):
    brain = progress_photo.user.brain

    update_data = {
        "progress_photos": {
            "last_photo": {
                "date": str(progress_photo.date),
                "metrics": progress_photo.metrics,
                "ai_analysis": progress_photo.ai_analysis,
            }
        }
    }

    brain.data = deep_merge_dict(
        brain.data,
        update_data,
    )

    brain.save()
