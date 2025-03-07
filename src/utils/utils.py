def constrain(n, low, high):
    """Constrain a value to a range"""
    return max(min(n, high), low)
