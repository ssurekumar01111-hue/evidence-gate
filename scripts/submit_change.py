#!/usr/bin/env python3
"""
CLI script to submit a ChangeRequest to Evidence Gate.
Can post to running API server or execute the evaluation pipeline directly.
"""
import sys
import json
import argparse
from pathlib import Path
import urllib.request
import urllib.error

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.api.schemas import ChangeRequest
from src.discovery.parser import parse_change_request
from src.evidence.collector import build_evidence_bundle
from src.decision.risk_engine import evaluate_risk
from src.validation.engine import validate_revenue_compatibility
from src.decision.evaluator import build_decision_receipt
from src.writeback.writer import write_decision_provenance


def main():
    parser = argparse.ArgumentParser(description="Submit a ChangeRequest payload to Evidence Gate.")
    parser.add_argument(
        "--fixture",
        default="fixtures/net_revenue_rename.json",
        help="Path to ChangeRequest JSON payload fixture",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000/evaluate",
        help="API URL endpoint (falls back to local pipeline if server unreachable)",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON DecisionReceipt")
    args = parser.parse_args()

    req = parse_change_request(args.fixture)

    # Try sending to running API first
    payload = json.dumps(req.model_dump()).encode("utf-8")
    request = urllib.request.Request(
        args.api_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    receipt_dict = None
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            if response.status == 200:
                receipt_dict = json.loads(response.read().decode("utf-8"))
    except Exception:
        # Fallback to direct pipeline execution
        evidence = build_evidence_bundle(req)
        risk = evaluate_risk(req, evidence)
        val = validate_revenue_compatibility()
        receipt = build_decision_receipt(req, evidence, risk, val)
        write_decision_provenance(receipt)
        receipt_dict = receipt.model_dump()

    if args.json:
        print(json.dumps(receipt_dict, indent=2))
        return

    print("=" * 80)
    print("EVIDENCE GATE — CHANGE REQUEST SUBMISSION RESULT")
    print("=" * 80)
    print(f"Change ID:         {receipt_dict.get('decision_id')}")
    print(f"Decision Status:   {receipt_dict.get('status', '').upper()}")
    print(f"Numeric Risk:      {receipt_dict.get('risk_score')}/100")
    print(f"PR / Change URL:   {receipt_dict.get('change_url')}")
    print("-" * 80)
    print(f"Rationale:\n  {receipt_dict.get('business_rationale')}")
    print("-" * 80)
    print(f"Required Approvers:")
    for app in receipt_dict.get("required_approvers", []):
        print(f"  - {app}")
    if receipt_dict.get("unowned_assets_needing_escalation"):
        print("-" * 80)
        print(f"Unowned Assets Needing Escalation:")
        for unowned in receipt_dict.get("unowned_assets_needing_escalation", []):
            print(f"  - {unowned}")
    print("-" * 80)
    print(f"Recommended Action:\n  {receipt_dict.get('recommended_action')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
