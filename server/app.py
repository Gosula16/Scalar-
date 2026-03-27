"""FastAPI application for Smart Support Env."""

from dataclasses import asdict
from typing import Any, Dict

from fastapi import Body, FastAPI, HTTPException

try:
    from ..support_models import SmartSupportAction
    from .environment import SmartSupportEnvironment
except ImportError:
    from server.environment import SmartSupportEnvironment
    from support_models import SmartSupportAction

app = FastAPI(title="Smart Support Env", version="3.0.0")
env = SmartSupportEnvironment()


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "name": "smart-support-env",
        "status": "ready",
        "description": "Real-world customer support environment with three graded tasks.",
        "endpoints": ["/reset", "/step", "/state", "/tasks", "/health", "/docs"],
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "healthy"}


@app.get("/tasks")
async def list_tasks() -> Any:
    return env.tasks()


@app.post("/reset")
async def reset(request: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    try:
        observation = env.reset(task_name=request.get("task_name", "basic_greeting"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"observation": asdict(observation), "reward": None, "done": False}


@app.post("/step")
async def step(request: Dict[str, Any]) -> Dict[str, Any]:
    try:
        action = SmartSupportAction(**request.get("action", {}))
        observation = env.step(action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "observation": asdict(observation),
        "reward": observation.reward,
        "done": observation.done,
    }


@app.get("/state")
async def state() -> Dict[str, Any]:
    try:
        return asdict(env.state)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
