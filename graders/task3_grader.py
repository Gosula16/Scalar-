from models.state import EnvironmentState, TicketStatus


def grade_advanced_escalation(state: EnvironmentState) -> float:
    completed = sum(1 for objective in state.completed_objectives if objective.achieved)
    score = completed / max(len(state.completed_objectives), 1)
    if state.status in {TicketStatus.ESCALATED, TicketStatus.CLOSED}:
        score += 0.1
    score -= min(state.unsafe_action_count * 0.15, 0.3)
    return max(0.0, min(score, 1.0))
