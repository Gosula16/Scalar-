from typing import List

from pydantic import BaseModel, Field

from models.state import ConversationTurn, CustomerTicket, TicketStatus


class EnvironmentObservation(BaseModel):
    task_name: str
    task_difficulty: str
    task_title: str
    instructions: str
    current_ticket: CustomerTicket
    conversation_history: List[ConversationTurn] = Field(default_factory=list)
    status: TicketStatus
    step_count: int
    remaining_steps: int
    latest_customer_message: str
    available_actions: List[str]
