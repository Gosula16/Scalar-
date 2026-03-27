from pydantic import BaseModel


class StepReward(BaseModel):
    value: float
    progress: float
    penalty: float
    explanation: str
    grader_score: float
