from datetime import datetime, timezone, timedelta
from typing import Optional
from src.api.schemas import ChangeRequest, DecisionReceipt, ValidationResult
from src.evidence.schemas import EvidenceBundle
from src.decision.schemas import RiskAssessment
from src.validation.schemas import RevenueValidationReport


def build_decision_receipt(
    change_request: ChangeRequest,
    evidence: EvidenceBundle,
    risk_assessment: RiskAssessment,
    validation_report: RevenueValidationReport,
    decision_id: str = "eg-2026-001",
) -> DecisionReceipt:
    """
    Combines Milestone 2 risk assessment and Milestone 3 metric validation report
    into a complete, deterministic DecisionReceipt artifact.
    """
    now = datetime.now(timezone.utc)
    graph_snapshot_at = now.isoformat()
    revalidate_after = (now + timedelta(days=30)).isoformat()

    evidence_checked = [
        "schema_diff",
        "dataset_ownership",
        "glossary_terms",
        "downstream_lineage",
        "quality_assertions",
        "revenue_compatibility_query",
    ]

    invalidation_inputs = [
        f"dataset_schema:{change_request.source_asset}",
        f"glossary_term_link:{change_request.source_asset}",
        f"downstream_lineage:{change_request.source_asset}",
        f"quality_assertion:{change_request.source_asset}",
    ]

    # Combination Rule: A metric validation failure is a hard block that overrides the Milestone 2 preliminary risk score and sets risk_score=100 and status="blocked" regardless of initial risk score.
    if validation_report.result == "failed":
        final_status = "blocked"
        final_risk_score = 100
        business_rationale = (
            f"Change BLOCKED: Field rename '{change_request.old_field}' -> '{change_request.new_field}' "
            f"causes a metric discrepancy. {validation_report.reason}"
        )
        recommended_action = (
            "Apply the generated dbt compatibility patch (examples/recognized_revenue_patch.sql) "
            "and execute migration test suite (examples/test_recognized_revenue_migration.py) "
            "before re-submitting for approval."
        )
    elif risk_assessment.leaning == "blocked":
        final_status = "blocked"
        final_risk_score = 100
        business_rationale = f"Change BLOCKED: {risk_assessment.rationale}"
        recommended_action = "Resolve deterministic risk violations prior to validation."
    elif risk_assessment.risk_score >= 50:
        final_status = "needs-review"
        final_risk_score = risk_assessment.risk_score
        business_rationale = f"Change NEEDS REVIEW: {risk_assessment.rationale}"
        recommended_action = (
            f"Obtain approval from listed approvers: {', '.join(risk_assessment.required_approvers)}"
        )
    else:
        final_status = "approved"
        final_risk_score = risk_assessment.risk_score
        business_rationale = f"Change APPROVED: {risk_assessment.rationale}"
        recommended_action = "Proceed with schema migration and update downstream models."

    val_res = ValidationResult(
        result=validation_report.result,
        reason=validation_report.reason,
    )

    return DecisionReceipt(
        decision_id=decision_id,
        status=final_status,
        change_url=change_request.pr_url,
        business_rationale=business_rationale,
        affected_assets=[change_request.source_asset],
        graph_snapshot_at=graph_snapshot_at,
        risk_score=final_risk_score,
        evidence_checked=evidence_checked,
        validation=val_res,
        required_approvers=risk_assessment.required_approvers,
        recommended_action=recommended_action,
        revalidate_after=revalidate_after,
        invalidation_inputs=invalidation_inputs,
    )
