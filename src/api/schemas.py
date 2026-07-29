from typing import List, Literal
from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    result: Literal["passed", "failed"]
    reason: str


class ChangeRequest(BaseModel):
    change_id: str
    change_type: Literal["field_rename"] = "field_rename"
    source_asset: str
    old_field: str
    new_field: str
    old_type: str
    new_type: str
    pr_url: str


class DecisionReceipt(BaseModel):
    decision_id: str
    status: Literal["needs-review", "approved", "blocked"]
    change_url: str
    business_rationale: str
    affected_assets: List[str]
    graph_snapshot_at: str
    risk_score: int = Field(ge=0, le=100)
    evidence_checked: List[str]
    validation: ValidationResult
    required_approvers: List[str]
    recommended_action: str
    revalidate_after: str
    invalidation_inputs: List[str]
