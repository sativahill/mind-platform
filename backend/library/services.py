from brain.services import deep_merge_dict


def update_brain_from_book(book):
    brain = book.user.brain

    update_data = {
        "library": {
            "last_book": {
                "title": book.title,
                "progress": book.progress,
                "is_completed": book.is_completed,
            }
        }
    }

    brain.data = deep_merge_dict(
        brain.data,
        update_data,
    )

    brain.save()
