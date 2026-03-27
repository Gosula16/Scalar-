from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    GREET = "greet"
    EMPATHIZE = "empathize"
    ASK_CLARIFYING_QUESTION = "ask_clarifying_question"
    TROUBLESHOOT = "troubleshoot"
    RESOLVE = "resolve"
    ESCALATE = "escalate"
    CLOSE_TICKET = "close_ticket"
    UPDATE_STATUS = "update_status"


class AgentAction(BaseModel):
    action_type: ActionType
    content: str = Field(..., min_length=8, description="Agent message to the customer")
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    tags: List[str] = Field(default_factory=list)
    resolution_code: Optional[str] = Field(
        default=None,
        description="Optional internal resolution or escalation code.",
    )
