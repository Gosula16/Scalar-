try:
    from ..models.state import EnvironmentState, TicketStatus
    from .common import strict_unit_interval
except ImportError:
    from models.state import EnvironmentState, TicketStatus
    from graders.common import strict_unit_interval


def grade_basic_greeting(state: EnvironmentState) -> float:
    completed = sum(1 for objective in state.completed_objectives if objective.achieved)
    score = completed / max(len(state.completed_objectives), 1)
    if state.status in {TicketStatus.RESOLVED, TicketStatus.CLOSED}:
        score += 0.1
    score -= min(state.repeated_action_count * 0.05, 0.1)
    return strict_unit_interval(score)
