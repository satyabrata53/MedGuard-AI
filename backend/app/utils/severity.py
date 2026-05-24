SEVERITY_IMPORTANCE = {
    "HARD_BLOCK": 10,
    "SEVERE": 8,
    "MODERATE": 5,
    "MINOR": 2,
}


def importance_for(severity: str) -> int:
    return SEVERITY_IMPORTANCE.get(severity, 1)
