from models.state import EnvironmentState, TicketStatus


def grade_basic_greeting(state: EnvironmentState) -> float:
    completed = sum(1 for objective in state.completed_objectives if objective.achieved)
    score = completed / max(len(state.completed_objectives), 1)
    if state.status in {TicketStatus.RESOLVED, TicketStatus.CLOSED}:
        score += 0.1
    score -= min(state.repeated_action_count * 0.05, 0.1)
    return max(0.0, min(score, 1.0))
