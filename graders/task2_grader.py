try:
    from ..models.state import EnvironmentState, TicketStatus
except ImportError:
    from models.state import EnvironmentState, TicketStatus


def grade_medium_resolution(state: EnvironmentState) -> float:
    completed = sum(1 for objective in state.completed_objectives if objective.achieved)
    score = completed / max(len(state.completed_objectives), 1)
    if state.status == TicketStatus.CLOSED:
        score += 0.1
    if state.unsafe_action_count:
        score -= 0.1 * state.unsafe_action_count
    return max(0.0, min(score, 1.0))
