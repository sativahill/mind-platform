from copy import deepcopy

from django.db import transaction

from .models import Brain


def deep_merge_dict(original, new_data):
    """Return a deep merge without mutating either input object."""
    merged = deepcopy(original)

    for key, value in new_data.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge_dict(
                merged[key],
                value,
            )
        else:
            merged[key] = deepcopy(value)

    return merged


def update_brain_data(*, user, patch):
    """Merge a trusted patch into the latest locked Brain row."""
    if not isinstance(patch, dict):
        raise TypeError("Brain patch must be a dictionary.")

    with transaction.atomic():
        brain = (
            Brain.objects
            .select_for_update()
            .get(user=user)
        )
        brain.data = deep_merge_dict(
            brain.data or {},
            patch,
        )
        brain.save(update_fields=["data"])

    return brain
