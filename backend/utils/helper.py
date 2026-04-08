def normalize_name(name):
    """Normalize medicine name for comparison."""
    return name.strip().lower()


def get_severity_order(severity):
    """Return numeric priority for severity (higher = more severe)."""
    return {"safe": 0, "moderate": 1, "dangerous": 2}.get(severity, 0)
