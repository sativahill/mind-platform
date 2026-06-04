def deep_merge_dict(original, new_data):
    for key, value in new_data.items():

        if(
            key in original
            and isinstance(original[key], dict)
            and isinstance(value, dict)
        ):
            deep_merge_dict(original[key], value)

        else:
            original[key] = value

    return original