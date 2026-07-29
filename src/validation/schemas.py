from typing import Literal
from pydantic import BaseModel
from src.api.schemas import ValidationResult


class RevenueValidationReport(ValidationResult):
    old_aggregate: float
    proposed_aggregate: float
    delta_pct: float
    tolerance_pct: float = 1.0
