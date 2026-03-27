from typing import Dict

try:
    from openenv.core.client_types import StepResult
    from openenv.core.http_env_client import HTTPEnvClient
except ImportError:
    from openenv_core.client_types import StepResult
    from openenv_core.http_env_client import HTTPEnvClient

try:
    from .support_models import SmartSupportAction, SmartSupportObservation, SmartSupportState
except ImportError:
    from support_models import SmartSupportAction, SmartSupportObservation, SmartSupportState


class SmartSupportEnv(HTTPEnvClient[SmartSupportAction, SmartSupportObservation]):
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
