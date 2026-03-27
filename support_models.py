from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from openenv.core.env_server.types import Action, Observation, State
except ImportError:
    from openenv_core.env_server.types import Action, Observation, State


@dataclass(kw_only=True)
class SmartSupportAction(Action):
    action_type: str
    content: str
    confidence: float = 0.75
    tags: List[str] = field(default_factory=list)
    resolution_code: Optional[str] = None


@dataclass(kw_only=True)
class SmartSupportObservation(Observation):
    task_name: str = "basic_greeting"
    task_difficulty: str = "easy"
    task_title: str = ""
    instructions: str = ""
    current_ticket: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    status: str = "open"
    step_count: int = 0
    remaining_steps: int = 0
    latest_customer_message: str = ""
    available_actions: List[str] = field(default_factory=list)
    grader_score: float = 0.0
    completed_objectives: int = 0
    total_objectives: int = 0


@dataclass
class SmartSupportState(State):
    episode_id: str = ""
    step_count: int = 0
    task_name: str = "basic_greeting"
    task_difficulty: str = "easy"
    task_title: str = ""
    instructions: str = ""
    current_ticket: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    status: str = "open"
    max_steps: int = 0
    customer_response: str = ""
    completed_objectives: List[Dict[str, Any]] = field(default_factory=list)
    stage_index: int = 0
    total_reward: float = 0.0
    grader_score: float = 0.0
    done: bool = False
    last_outcome: str = ""
    repeated_action_count: int = 0
    unsafe_action_count: int = 0
