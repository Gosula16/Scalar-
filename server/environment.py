from __future__ import annotations

from copy import deepcopy
from typing import Dict, List
from uuid import uuid4

try:
    from ..graders.task1_grader import grade_basic_greeting
    from ..graders.task2_grader import grade_medium_resolution
    from ..graders.task3_grader import grade_advanced_escalation
    from ..support_models import SmartSupportAction, SmartSupportObservation, SmartSupportState
    from ..tasks.catalog import TASKS, get_task_names
except ImportError:
    from graders.task1_grader import grade_basic_greeting
    from graders.task2_grader import grade_medium_resolution
    from graders.task3_grader import grade_advanced_escalation
    from support_models import SmartSupportAction, SmartSupportObservation, SmartSupportState
    from tasks.catalog import TASKS, get_task_names


TASK_GRADERS = {
    "basic_greeting": grade_basic_greeting,
    "medium_resolution": grade_medium_resolution,
    "advanced_escalation": grade_advanced_escalation,
}

AVAILABLE_ACTIONS = [
    "greet",
    "empathize",
    "ask_clarifying_question",
    "troubleshoot",
    "resolve",
    "escalate",
    "close_ticket",
    "update_status",
]


class SmartSupportEnvironment:
    def __init__(self) -> None:
        self._active_task: Dict = {}
        self._state: SmartSupportState | None = None
        self._last_action_signature = ""

    def reset(self, task_name: str = "basic_greeting") -> SmartSupportObservation:
        if task_name not in TASKS:
            raise ValueError(f"Invalid task name: {task_name}")

        self._active_task = deepcopy(TASKS[task_name])
        objectives = [
            {
                "name": item["name"],
                "description": item["description"],
                "achieved": False,
                "achieved_on_step": None,
                "evidence": "",
            }
            for item in self._active_task["objectives"]
        ]
        initial_message = self._active_task["initial_customer_message"]
        self._state = SmartSupportState(
            episode_id=str(uuid4()),
            step_count=0,
            task_name=task_name,
            task_difficulty=self._active_task["difficulty"],
            task_title=self._active_task["title"],
            instructions=self._active_task["instructions"],
            current_ticket=self._active_task["ticket"].model_dump(),
            conversation_history=[{"speaker": "customer", "message": initial_message}],
            status="open",
            max_steps=self._active_task["max_steps"],
            customer_response=initial_message,
            completed_objectives=objectives,
            stage_index=0,
            total_reward=0.0,
            grader_score=0.0,
            done=False,
            last_outcome="Environment reset.",
            repeated_action_count=0,
            unsafe_action_count=0,
        )
        self._last_action_signature = ""
        return self._to_observation(reward=None, done=False)

    def step(self, action: SmartSupportAction) -> SmartSupportObservation:
        if self._state is None:
            raise ValueError("Call reset() first.")
        if self._state.done:
            raise ValueError("Episode already finished. Call reset() first.")

        self._state.step_count += 1
        self._state.conversation_history.append(
            {"speaker": "agent", "message": action.content}
        )

        repeated = self._check_repeated_action(action)
        progress, penalty, explanation, success = self._evaluate_stage(action)
        if repeated:
            penalty += 0.1
            explanation = f"{explanation} Repeated the previous action.".strip()

        current_objective = self._active_task["objectives"][self._state.stage_index]

        if success:
            objective_state = self._state.completed_objectives[self._state.stage_index]
            objective_state["achieved"] = True
            objective_state["achieved_on_step"] = self._state.step_count
            objective_state["evidence"] = action.content
            self._state.status = current_objective["status_on_success"]
            self._state.customer_response = current_objective["customer_reply"]
            self._state.stage_index += 1
            self._state.last_outcome = f"Objective completed: {current_objective['name']}"
        else:
            self._state.customer_response = (
                "I still need clearer help on this issue. Please address the request directly."
            )
            self._state.last_outcome = "Objective not completed."

        self._state.conversation_history.append(
            {"speaker": "customer", "message": self._state.customer_response}
        )

        if self._state.stage_index >= len(self._active_task["objectives"]):
            self._state.done = True
        if self._state.step_count >= self._state.max_steps:
            self._state.done = True

        grader = TASK_GRADERS[self._state.task_name]
        self._state.grader_score = grader(self._grader_state())
        reward_value = round(progress - penalty, 4)
        self._state.total_reward = round(self._state.total_reward + reward_value, 4)

        if self._state.done and self._state.status not in {"closed", "resolved", "escalated"}:
            self._state.status = "resolved" if self._state.grader_score >= 0.6 else "in_progress"

        return self._to_observation(reward=reward_value, done=self._state.done, explanation=explanation)

    @property
    def state(self) -> SmartSupportState:
        if self._state is None:
            raise ValueError("Call reset() first.")
        return self._state

    def tasks(self) -> List[Dict[str, str]]:
        return [
            {
                "task_name": name,
                "difficulty": TASKS[name]["difficulty"],
                "title": TASKS[name]["title"],
            }
            for name in get_task_names()
        ]

    def _to_observation(
        self, reward: float | None, done: bool, explanation: str = ""
    ) -> SmartSupportObservation:
        assert self._state is not None
        return SmartSupportObservation(
            task_name=self._state.task_name,
            task_difficulty=self._state.task_difficulty,
            task_title=self._state.task_title,
            instructions=self._state.instructions,
            current_ticket=self._state.current_ticket,
            conversation_history=self._state.conversation_history,
            status=self._state.status,
            step_count=self._state.step_count,
            remaining_steps=max(self._state.max_steps - self._state.step_count, 0),
            latest_customer_message=self._state.customer_response,
            available_actions=AVAILABLE_ACTIONS,
            grader_score=round(self._state.grader_score, 4),
            completed_objectives=sum(
                1 for item in self._state.completed_objectives if item["achieved"]
            ),
            total_objectives=len(self._state.completed_objectives),
            reward=reward,
            done=done,
            metadata={
                "total_reward": self._state.total_reward,
                "last_outcome": self._state.last_outcome,
                "explanation": explanation or "Step processed.",
            },
        )

    def _check_repeated_action(self, action: SmartSupportAction) -> bool:
        assert self._state is not None
        action_signature = f"{action.action_type}:{action.content.strip().lower()}"
        repeated = action_signature == self._last_action_signature
        if repeated:
            self._state.repeated_action_count += 1
        self._last_action_signature = action_signature
        return repeated

    def _evaluate_stage(self, action: SmartSupportAction) -> tuple[float, float, str, bool]:
        assert self._state is not None
        current_objective = self._active_task["objectives"][self._state.stage_index]
        progress = 0.0
        penalty = 0.0
        explanation_parts: List[str] = []
        success = True
        content_lower = action.content.lower()

        if action.action_type not in current_objective["accepted_action_types"]:
            penalty += 0.2
            success = False
            explanation_parts.append("Action type did not match the next workflow step.")

        if not all(keyword.lower() in content_lower for keyword in current_objective["required_keywords"]):
            penalty += 0.15
            success = False
            explanation_parts.append("Response missed one or more required support details.")

        required_code = current_objective.get("required_resolution_code")
        if required_code and action.resolution_code != required_code:
            penalty += 0.2
            success = False
            explanation_parts.append("Escalation was missing the correct billing reason code.")

        if self._state.task_name == "advanced_escalation" and "refund" in content_lower:
            if action.action_type != "escalate":
                penalty += 0.15
                self._state.unsafe_action_count += 1
                success = False
                explanation_parts.append(
                    "Promised a billing outcome without the correct escalation flow."
                )

        if action.confidence < 0.35:
            penalty += 0.05
            explanation_parts.append("Low confidence reduced the reward slightly.")

        if success:
            progress = current_objective["progress"]
            explanation_parts.append(
                f"Completed objective: {current_objective['name']}."
            )

        return progress, penalty, " ".join(explanation_parts).strip(), success

    def _grader_state(self):
        try:
            from ..models.state import EnvironmentState
        except ImportError:
            from models.state import EnvironmentState

        assert self._state is not None
        return EnvironmentState(
            task_name=self._state.task_name,
            task_difficulty=self._state.task_difficulty,
            task_title=self._state.task_title,
            instructions=self._state.instructions,
            current_ticket=self._active_task["ticket"],
            conversation_history=self._state.conversation_history,
            status=self._state.status,
            step_count=self._state.step_count,
            max_steps=self._state.max_steps,
            customer_response=self._state.customer_response,
            completed_objectives=self._state.completed_objectives,
            stage_index=self._state.stage_index,
            total_reward=self._state.total_reward,
            grader_score=self._state.grader_score,
            done=self._state.done,
            last_outcome=self._state.last_outcome,
            repeated_action_count=self._state.repeated_action_count,
            unsafe_action_count=self._state.unsafe_action_count,
        )
