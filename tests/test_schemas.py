import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from src.api.schemas import ChangeRequest, DecisionReceipt, ValidationResult


def test_change_request_schema():
    payload = {
        "change_id": "test-001",
        "change_type": "field_rename",
        "source_asset": "urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details,PROD)",
        "old_field": "order_total",
        "new_field": "recognized_revenue",
        "old_type": "decimal",
        "new_type": "decimal",
        "pr_url": "https://github.com/example/repo/pull/42",
    }
    req = ChangeRequest(**payload)
    assert req.change_id == "test-001"
    assert req.change_type == "field_rename"
    assert req.old_field == "order_total"
    assert req.new_field == "recognized_revenue"


def test_change_request_fixture():
    fixture_path = Path("fixtures/net_revenue_rename.json")
    if not fixture_path.exists():
        pytest.skip("Fixture file does not exist yet")
    
    with open(fixture_path, "r") as f:
        data = json.load(f)
    
    req = ChangeRequest(**data)
    assert req.old_field == "order_total"
    assert req.new_field == "recognized_revenue"
    assert req.source_asset.startswith("urn:li:dataset:")


def test_decision_receipt_schema():
    payload = {
        "decision_id": "eg-2026-001",
        "status": "blocked",
        "change_url": "https://github.com/example/repo/pull/42",
        "business_rationale": "Field renaming causes revenue aggregate discrepancy.",
        "affected_assets": [
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details,PROD)"
        ],
        "graph_snapshot_at": "2026-07-27T11:00:00Z",
        "risk_score": 75,
        "evidence_checked": ["lineage", "ownership", "glossary"],
        "validation": {
            "result": "failed",
            "reason": "Weekly revenue aggregate shifted by 4.3%"
        },
        "required_approvers": ["Finance Analytics Owner"],
        "recommended_action": "Create compatibility view and re-run migration test",
        "revalidate_after": "2026-08-27T11:00:00Z",
        "invalidation_inputs": ["dataset_schema", "glossary_term_link"]
    }
    receipt = DecisionReceipt(**payload)
    assert receipt.decision_id == "eg-2026-001"
    assert receipt.status == "blocked"
    assert receipt.validation.result == "failed"
