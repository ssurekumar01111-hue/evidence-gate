#!/usr/bin/env python3
"""
CLI entry point for assess_change_risk skill.
Evaluates risk rules and metric validation for a proposed schema change request.
"""
import sys
import json
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.api.schemas import ChangeRequest
from src.discovery.parser import parse_change_request
from src.evidence.collector import build_evidence_bundle
from src.decision.risk_engine import evaluate_risk
from src.validation.engine import validate_revenue_compatibility
from src.decision.evaluator import build_decision_receipt


def main():
    parser = argparse.ArgumentParser(
        description="Assess risk and validate compatibility for a proposed schema change."
    )
    parser.add_argument(
        "--fixture",
        help="Path to ChangeRequest JSON fixture (e.g. fixtures/net_revenue_rename.json)",
    )
    parser.add_argument(
        "--urn",
        default="urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details,PROD)",
        help="Target asset URN on DataHub",
    )
    parser.add_argument("--old-field", default="order_total", help="Existing field name")
    parser.add_argument("--new-field", default="recognized_revenue", help="Proposed new field name")
    parser.add_argument("--old-type", default="decimal", help="Existing data type")
    parser.add_argument("--new-type", default="decimal", help="Proposed data type")
    parser.add_argument("--change-id", default="cr-risk-eval-001", help="Change Request ID")
    parser.add_argument("--pr-url", default="https://github.com/example/repo/pull/42", help="PR URL")
    parser.add_argument("--json", action="store_true", help="Output raw JSON DecisionReceipt")
    args = parser.parse_args()

    if args.fixture:
        req = parse_change_request(args.fixture)
    else:
        req = ChangeRequest(
            change_id=args.change_id,
            change_type="field_rename",
            source_asset=args.urn,
            old_field=args.old_field,
            new_field=args.new_field,
            old_type=args.old_type,
            new_type=args.new_type,
            pr_url=args.pr_url,
        )

    bundle = build_evidence_bundle(req)
    risk = evaluate_risk(req, bundle)
    val = validate_revenue_compatibility()
    receipt = build_decision_receipt(req, bundle, risk, val)

    if args.json:
        print(json.dumps(receipt.model_dump(), indent=2))
        return

    print("=" * 80)
    print("SKILL: ASSESS CHANGE RISK — EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Target Asset:   {req.source_asset}")
    print(f"Field Rename:   '{req.old_field}' -> '{req.new_field}'")
    print(f"PR URL:         {req.pr_url}")
    print("-" * 80)
    print(f"Risk Score:     {risk.risk_score}/100")
    print(f"Risk Leaning:   {risk.leaning.upper()}")
    print(f"Risk Signals:   {', '.join(risk.signals_triggered)}")
    print(f"Approvers:      {', '.join(risk.required_approvers)}")
    print("-" * 80)
    print(f"Validation:     {val.result.upper()}")
    print(f"Old Aggregate:  ${val.old_aggregate:,.2f}")
    print(f"Proposed Agg:   ${val.proposed_aggregate:,.2f}")
    print(f"Delta:          {val.delta_pct:.2f}% (Tolerance: {val.tolerance_pct:.2f}%)")
    print("-" * 80)
    print(f"FINAL DECISION: {receipt.status.upper()}")
    print(f"Rationale:\n  {receipt.business_rationale}")
    print("=" * 80)


if __name__ == "__main__":
    main()
