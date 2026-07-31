#!/usr/bin/env python3
"""
CLI script to query DataHub GMS for Decision Provenance stored on an asset URN.
Exits cleanly and prints the stored reasoning, status, evidence, and approvers.
"""
import sys
import json
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.writeback.retriever import retrieve_decision_provenance


def main():
    parser = argparse.ArgumentParser(
        description="Query DataHub for Decision Provenance on a dataset asset."
    )
    parser.add_argument(
        "--urn",
        default="urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details,PROD)",
        help="Target asset URN on DataHub",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    report = retrieve_decision_provenance(args.urn)

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print("=" * 80)
    print(f"EVIDENCE GATE — DECISION PROVENANCE RETRIEVAL")
    print(f"Target Asset URN: {args.urn}")
    print("=" * 80)

    if not report.get("has_provenance"):
        print(f"Status: NO PROVENANCE STORED ON DATAHUB")
        print(report.get("message", ""))
        return

    print(f"Decision ID:         {report.get('decision_id')}")
    print(f"Decision Outcome:    {report.get('status').upper()}")
    print(f"Provenance Status:   {report.get('provenance_status').upper()}")
    if report.get("stale_reason"):
        print(f"Staleness Reason:    {report.get('stale_reason')}")
    print(f"Numeric Risk Score:  {report.get('risk_score')}/100")
    print(f"PR / Change URL:     {report.get('change_url')}")
    print("-" * 80)
    print(f"WHY WAS THIS DECISION MADE?")
    print(f"Rationale:\n  {report.get('business_rationale')}")
    print(f"\nValidation Result:\n  {report.get('validation_reason')}")
    print("-" * 80)
    print(f"Required Approvers:")
    for app in report.get("required_approvers", []):
        print(f"  - {app}")
    if report.get("unowned_assets_needing_escalation"):
        print("-" * 80)
        print(f"Unowned Assets Needing Escalation:")
        for unowned in report.get("unowned_assets_needing_escalation", []):
            print(f"  - {unowned}")
    print("-" * 80)
    print(f"Recommended Action:\n  {report.get('recommended_action')}")
    print(f"Revalidate After Expiry: {report.get('revalidate_after')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
