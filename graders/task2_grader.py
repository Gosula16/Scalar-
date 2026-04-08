try:
    from ..models.state import EnvironmentState, TicketStatus
    from .common import strict_unit_interval
except ImportError:
    from models.state import EnvironmentState, TicketStatus
    from graders.common import strict_unit_interval


def grade_medium_resolution(state: EnvironmentState) -> float:
    completed = sum(1 for objective in state.completed_objectives if objective.achieved)
    score = completed / max(len(state.completed_objectives), 1)
    if state.status == TicketStatus.CLOSED:
        score += 0.1
    if state.unsafe_action_count:
        score -= 0.1 * state.unsafe_action_count
    return strict_unit_interval(score)
