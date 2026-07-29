#!/usr/bin/env python3
"""
CLI entry point for create_decision_provenance skill.
Writes Decision Provenance structured custom properties, documentation links, and operational incidents back to DataHub GMS.
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
from src.writeback.writer import write_decision_provenance


def main():
    parser = argparse.ArgumentParser(
        description="Write Decision Provenance metadata artifact back to DataHub GMS."
    )
    parser.add_argument(
        "--fixture",
        default="fixtures/net_revenue_rename.json",
        help="Path to ChangeRequest JSON fixture",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON write-back result")
    args = parser.parse_args()

    req = parse_change_request(args.fixture)
    bundle = build_evidence_bundle(req)
    risk = evaluate_risk(req, bundle)
    val = validate_revenue_compatibility()
    receipt = build_decision_receipt(req, bundle, risk, val)

    res = write_decision_provenance(receipt)

    if args.json:
        print(json.dumps(res, indent=2))
        return

    print("=" * 80)
    print("SKILL: CREATE DECISION PROVENANCE — WRITE-BACK SUCCESS")
    print("=" * 80)
    print(f"Target Asset URN:     {res['asset_urn']}")
    print(f"Decision ID:          {res['decision_id']}")
    print(f"Decision Status:      {res['status'].upper()}")
    print(f"Custom Props Emitted: {res['custom_properties_emitted']}")
    print(f"Documentation Link:   {res['documentation_link']}")
    print(f"Native Incident URN:  {res['incident_urn']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
