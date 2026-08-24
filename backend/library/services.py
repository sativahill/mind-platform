from brain.services import update_brain_data


def update_brain_from_book(book):
    update_data = {
        "library": {
            "last_book": {
                "title": book.title,
                "progress": book.progress,
                "is_completed": book.is_completed,
            }
        }
    }

    update_brain_data(
        user=book.user,
        patch=update_data,
    )
