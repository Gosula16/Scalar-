from dataclasses import dataclass
from typing import Dict, Generic, TypeVar

import requests

try:
    from .support_models import SmartSupportAction, SmartSupportObservation, SmartSupportState
except ImportError:
    from support_models import SmartSupportAction, SmartSupportObservation, SmartSupportState


ObsT = TypeVar("ObsT")


@dataclass
class StepResult(Generic[ObsT]):
    observation: ObsT
    reward: float | None = None
    done: bool = False


class HTTPEnvClient:
    def __init__(self, base_url: str, request_timeout_s: float = 15.0):
        self._base = base_url.rstrip("/")
        self._timeout = float(request_timeout_s)
        self._http = requests.Session()


class SmartSupportEnv(HTTPEnvClient):
    def reset(self) -> StepResult[SmartSupportObservation]:
        response = self._http.post(f"{self._base}/reset", json={}, timeout=self._timeout)
        response.raise_for_status()
        return self._parse_result(response.json())

    def step(self, action: SmartSupportAction) -> StepResult[SmartSupportObservation]:
        response = self._http.post(
            f"{self._base}/step",
            json={"action": self._step_payload(action)},
            timeout=self._timeout,
        )
        response.raise_for_status()
        return self._parse_result(response.json())

    def state(self) -> SmartSupportState:
        response = self._http.get(f"{self._base}/state", timeout=self._timeout)
        response.raise_for_status()
        return self._parse_state(response.json())

    def _step_payload(self, action: SmartSupportAction) -> Dict:
        return {
            "action_type": action.action_type,
            "content": action.content,
            "confidence": action.confidence,
            "tags": action.tags,
            "resolution_code": action.resolution_code,
        }

    def _parse_result(self, payload: Dict) -> StepResult[SmartSupportObservation]:
        observation = SmartSupportObservation(
            **payload.get("observation", {}),
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> SmartSupportState:
        return SmartSupportState(**payload)
