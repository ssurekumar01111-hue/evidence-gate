from typing import List, Literal
from pydantic import BaseModel, Field


class RiskAssessment(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    leaning: Literal["needs-review", "approved", "blocked"]
    signals_triggered: List[str] = Field(default_factory=list)
    required_approvers: List[str] = Field(default_factory=list)
    rationale: str
