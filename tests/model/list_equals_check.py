def check_lists_equal(list_1: list, list_2: list) -> bool:
    """Check if two lists are equal."""
    return len(list_1) == len(list_2) and sorted(list_1) == sorted(list_2)
