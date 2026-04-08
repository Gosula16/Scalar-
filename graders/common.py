EPSILON = 0.001


def strict_unit_interval(score: float) -> float:
    return min(max(score, EPSILON), 1.0 - EPSILON)
