from copy import deepcopy
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from graders.task1_grader import grade_basic_greeting
from graders.task2_grader import grade_medium_resolution
from graders.task3_grader import grade_advanced_escalation
from models.action import AgentAction, ActionType
from models.observation import EnvironmentObservation
from models.reward import StepReward
from models.state import ConversationTurn, EnvironmentState, ObjectiveProgress, TicketStatus
from tasks.catalog import TASKS, get_task_names

app = FastAPI(title="Smart Support Env", version="2.0.0")


class ResetRequest(BaseModel):
    task_name: str = "basic_greeting"


class StepRequest(BaseModel):
    action: AgentAction


TASK_GRADERS = {
    "basic_greeting": grade_basic_greeting,
    "medium_resolution": grade_medium_resolution,
    "advanced_escalation": grade_advanced_escalation,
}

ACTIVE_TASK: Dict = {}
env_state: EnvironmentState | None = None
last_action_signature: str = ""


def _status_from_string(value: str) -> TicketStatus:
    return TicketStatus(value)


def _build_state(task_name: str) -> EnvironmentState:
    task = deepcopy(TASKS[task_name])
    objectives = [
        ObjectiveProgress(name=item["name"], description=item["description"])
        for item in task["objectives"]
    ]
    initial_message = task["initial_customer_message"]
    return EnvironmentState(
        task_name=task_name,
        task_difficulty=task["difficulty"],
        task_title=task["title"],
        instructions=task["instructions"],
        current_ticket=task["ticket"],
        conversation_history=[ConversationTurn(speaker="customer", message=initial_message)],
        status=TicketStatus.OPEN,
        step_count=0,
        max_steps=task["max_steps"],
        customer_response=initial_message,
        completed_objectives=objectives,
        stage_index=0,
        total_reward=0.0,
        grader_score=0.0,
        done=False,
        last_outcome="Environment reset.",
    )


def _to_observation(state: EnvironmentState) -> EnvironmentObservation:
    return EnvironmentObservation(
        task_name=state.task_name,
        task_difficulty=state.task_difficulty,
        task_title=state.task_title,
        instructions=state.instructions,
        current_ticket=state.current_ticket,
        conversation_history=state.conversation_history,
        status=state.status,
        step_count=state.step_count,
        remaining_steps=max(state.max_steps - state.step_count, 0),
        latest_customer_message=state.customer_response,
        available_actions=[action.value for action in ActionType],
    )


def _contains_keywords(content: str, required_keywords: List[str]) -> bool:
    content_lower = content.lower()
    return all(keyword.lower() in content_lower for keyword in required_keywords)


def _evaluate_stage(action: AgentAction, state: EnvironmentState) -> tuple[float, float, str, bool]:
    task_objectives = ACTIVE_TASK["objectives"]
    current_objective = task_objectives[state.stage_index]
    progress = 0.0
    penalty = 0.0
    explanation_parts: List[str] = []
    success = True

    if action.action_type.value not in current_objective["accepted_action_types"]:
        penalty += 0.2
        success = False
        explanation_parts.append("Action type did not match the next workflow step.")

    if not _contains_keywords(action.content, current_objective["required_keywords"]):
        penalty += 0.15
        success = False
        explanation_parts.append("Response missed one or more required support details.")

    required_code = current_objective.get("required_resolution_code")
    if required_code and action.resolution_code != required_code:
        penalty += 0.2
        success = False
        explanation_parts.append("Escalation was missing the correct billing reason code.")

    if state.task_name == "advanced_escalation" and "refund" in action.content.lower():
        if action.action_type != ActionType.ESCALATE:
            penalty += 0.15
            state.unsafe_action_count += 1
            success = False
            explanation_parts.append("Promised a billing outcome without the correct escalation flow.")

    if action.confidence < 0.35:
        penalty += 0.05
        explanation_parts.append("Low confidence reduced the reward slightly.")

    if success:
        progress = current_objective["progress"]
        explanation_parts.append(f"Completed objective: {current_objective['name']}.")
    return progress, penalty, " ".join(explanation_parts).strip(), success


def _apply_action(action: AgentAction) -> tuple[EnvironmentObservation, StepReward, bool, Dict]:
    global env_state, last_action_signature

    if env_state is None:
        raise HTTPException(status_code=400, detail="Call reset() first.")
    if env_state.done:
        raise HTTPException(status_code=400, detail="Episode already finished. Call reset() to start a new task.")

    env_state.step_count += 1
    env_state.conversation_history.append(ConversationTurn(speaker="agent", message=action.content))

    action_signature = f"{action.action_type.value}:{action.content.strip().lower()}"
    repeated = action_signature == last_action_signature
    if repeated:
        env_state.repeated_action_count += 1
    last_action_signature = action_signature

    progress, penalty, explanation, success = _evaluate_stage(action, env_state)
    if repeated:
        penalty += 0.1
        explanation = f"{explanation} Repeated the previous action."

    task_objectives = ACTIVE_TASK["objectives"]
    current_objective = task_objectives[env_state.stage_index]

    if success:
        objective_state = env_state.completed_objectives[env_state.stage_index]
        objective_state.achieved = True
        objective_state.achieved_on_step = env_state.step_count
        objective_state.evidence = action.content
        env_state.status = _status_from_string(current_objective["status_on_success"])
        env_state.customer_response = current_objective["customer_reply"]
        env_state.stage_index += 1
        env_state.last_outcome = f"Objective completed: {current_objective['name']}"
    else:
        env_state.customer_response = (
            "I still need clearer help on this issue. Please address the request directly."
        )
        env_state.last_outcome = "Objective not completed."

    env_state.conversation_history.append(
        ConversationTurn(speaker="customer", message=env_state.customer_response)
    )

    if env_state.stage_index >= len(task_objectives):
        env_state.done = True
    if env_state.step_count >= env_state.max_steps:
        env_state.done = True

    grader = TASK_GRADERS[env_state.task_name]
    env_state.grader_score = grader(env_state)
    reward_value = round(progress - penalty, 4)
    env_state.total_reward = round(env_state.total_reward + reward_value, 4)

    if env_state.done and env_state.status not in {TicketStatus.CLOSED, TicketStatus.RESOLVED, TicketStatus.ESCALATED}:
        env_state.status = TicketStatus.RESOLVED if env_state.grader_score >= 0.6 else TicketStatus.IN_PROGRESS

    reward = StepReward(
        value=reward_value,
        progress=round(progress, 4),
        penalty=round(penalty, 4),
        explanation=explanation or "Step processed.",
        grader_score=round(env_state.grader_score, 4),
    )
    observation = _to_observation(env_state)
    info = {
        "task_name": env_state.task_name,
        "completed_objectives": sum(1 for item in env_state.completed_objectives if item.achieved),
        "total_objectives": len(env_state.completed_objectives),
        "total_reward": env_state.total_reward,
        "last_outcome": env_state.last_outcome,
    }
    return observation, reward, env_state.done, info


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "healthy"}


@app.get("/tasks")
async def list_tasks() -> List[Dict[str, str]]:
    return [
        {
            "task_name": name,
            "difficulty": TASKS[name]["difficulty"],
            "title": TASKS[name]["title"],
        }
        for name in get_task_names()
    ]


@app.post("/reset")
async def reset(request: ResetRequest) -> Dict:
    global env_state, ACTIVE_TASK, last_action_signature

    if request.task_name not in TASKS:
        raise HTTPException(status_code=400, detail=f"Invalid task name: {request.task_name}")

    ACTIVE_TASK = deepcopy(TASKS[request.task_name])
    env_state = _build_state(request.task_name)
    last_action_signature = ""
    return {
        "observation": _to_observation(env_state).model_dump(),
        "task": {
            "task_name": request.task_name,
            "difficulty": ACTIVE_TASK["difficulty"],
            "title": ACTIVE_TASK["title"],
        },
    }


@app.post("/step")
async def step(request: StepRequest) -> Dict:
    observation, reward, done, info = _apply_action(request.action)
    return {
        "observation": observation.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info,
    }


@app.get("/state")
async def get_state() -> Dict:
    if env_state is None:
        raise HTTPException(status_code=400, detail="Call reset() first.")
    return env_state.model_dump()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
