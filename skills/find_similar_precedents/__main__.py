#!/usr/bin/env python3
"""
CLI entry point for find_similar_precedents skill.
Searches DataHub graph for prior decision artifacts and produces explicit 'What Still Applies / What Differs' comparison.
"""
import sys
import json
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.api.schemas import ChangeRequest
from src.precedent.retriever import find_precedent_decisions


def main():
    parser = argparse.ArgumentParser(
        description="Search DataHub graph for prior decision precedents for a proposed change."
    )
    parser.add_argument(
        "--urn",
        default="urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details_replica,PROD)",
        help="Candidate dataset URN on DataHub",
    )
    parser.add_argument("--old-field", default="order_total", help="Existing field name")
    parser.add_argument("--new-field", default="recognized_revenue", help="Proposed field name")
    parser.add_argument("--change-id", default="cr-precedent-check-002", help="Change ID")
    parser.add_argument("--pr-url", default="https://github.com/example/repo/pull/105", help="PR URL")
    parser.add_argument("--json", action="store_true", help="Output raw JSON precedent search results")
    args = parser.parse_args()

    req = ChangeRequest(
        change_id=args.change_id,
        change_type="field_rename",
        source_asset=args.urn,
        old_field=args.old_field,
        new_field=args.new_field,
        old_type="decimal",
        new_type="decimal",
        pr_url=args.pr_url,
    )

    res = find_precedent_decisions(req)

    if args.json:
        print(json.dumps(res, indent=2))
        return

    print("=" * 80)
    print("SKILL: FIND SIMILAR PRECEDENTS — SEARCH RESULTS")
    print("=" * 80)
    print(f"Candidate Change ID:   {res['candidate_change_id']}")
    print(f"Candidate Target Asset: {res['candidate_source_asset']}")
    print(f"Precedents Found:       {res['precedents_found_count']}")
    print("-" * 80)
    for p in res.get("precedents", []):
        print(f"Precedent Decision ID:  {p['precedent_decision_id']} (Prior Outcome: {p['prior_status'].upper()})")
        print(f"Prior Target Asset:     {p['prior_asset_urn']}")
        print(f"Prior Risk Score:       {p['prior_risk_score']}/100")
        print("\nWhat Still Applies:")
        for item in p["what_still_applies"]:
            print(f"  - {item}")
        print("\nWhat Differs:")
        for item in p["what_differs"]:
            print(f"  - {item}")
        print("\nReused Evidence:")
        for item in p["reused_evidence"]:
            print(f"  - {item}")
    print("=" * 80)


if __name__ == "__main__":
    main()
