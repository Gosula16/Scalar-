from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_ON_CUSTOMER = "waiting_on_customer"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class CustomerTicket(BaseModel):
    id: str
    customer_name: str
    category: str
    description: str
    priority: str
    account_tier: str
    sentiment: str
    business_impact: str


class ConversationTurn(BaseModel):
    speaker: str
    message: str


class ObjectiveProgress(BaseModel):
    name: str
    description: str
    achieved: bool = False
    achieved_on_step: Optional[int] = None
    evidence: str = ""


class EnvironmentState(BaseModel):
    task_name: str
    task_difficulty: str
    task_title: str
    instructions: str
    current_ticket: CustomerTicket
    conversation_history: List[ConversationTurn] = Field(default_factory=list)
    status: TicketStatus = TicketStatus.OPEN
    step_count: int = 0
    max_steps: int = 4
    customer_response: str = ""
    completed_objectives: List[ObjectiveProgress] = Field(default_factory=list)
    stage_index: int = 0
    total_reward: float = 0.0
    grader_score: float = 0.0
    done: bool = False
    last_outcome: str = ""
    repeated_action_count: int = 0
    unsafe_action_count: int = 0
