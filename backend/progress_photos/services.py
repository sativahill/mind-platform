from brain.services import update_brain_data


def update_brain_from_progress_photo(progress_photo):
    update_data = {
        "progress_photos": {
            "last_photo": {
                "date": str(progress_photo.date),
                "metrics": progress_photo.metrics,
                "ai_analysis": progress_photo.ai_analysis,
            }
        }
    }

    update_brain_data(
        user=progress_photo.user,
        patch=update_data,
    )
