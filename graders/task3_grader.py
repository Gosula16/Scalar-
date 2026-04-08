try:
    from ..models.state import EnvironmentState, TicketStatus
    from .common import strict_unit_interval
except ImportError:
    from models.state import EnvironmentState, TicketStatus
    from graders.common import strict_unit_interval


def grade_advanced_escalation(state: EnvironmentState) -> float:
    completed = sum(1 for objective in state.completed_objectives if objective.achieved)
    score = completed / max(len(state.completed_objectives), 1)
    if state.status in {TicketStatus.ESCALATED, TicketStatus.CLOSED}:
        score += 0.1
    score -= min(state.unsafe_action_count * 0.15, 0.3)
    return strict_unit_interval(score)
