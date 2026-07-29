#!/usr/bin/env python3
"""
CLI entry point for invalidate_stale_provenance skill.
Inspects DataHub live graph metadata against stored Decision Provenance snapshots and updates status to 'stale' on DataHub GMS if dependencies changed.
"""
import sys
import json
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.invalidation.watcher import (
    simulate_graph_change,
    check_and_invalidate_provenance,
    restore_glossary_terms,
)


def main():
    parser = argparse.ArgumentParser(
        description="Inspect DataHub graph and invalidate stale Decision Provenance artifacts."
    )
    parser.add_argument(
        "--urn",
        default="urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details,PROD)",
        help="Target dataset URN on DataHub",
    )
    parser.add_argument(
        "--simulate-remove-glossary",
        action="store_true",
        help="Simulate a real graph mutation (remove Revenue glossary term) before checking",
    )
    parser.add_argument(
        "--restore-terms",
        action="store_true",
        help="Restore original dataset glossary terms on DataHub",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON result")
    args = parser.parse_args()

    if args.restore_terms:
        restore_glossary_terms(args.urn)
        print(f"Restored original glossary terms for asset: {args.urn}")
        return

    if args.simulate_remove_glossary:
        sim_res = simulate_graph_change(args.urn, action="remove_glossary_term")
        print(f"[Simulated Graph Mutation] Removed term: {sim_res['removed_term_urn']}")

    res = check_and_invalidate_provenance(args.urn)

    if args.json:
        print(json.dumps(res, indent=2))
        return

    print("=" * 80)
    print("SKILL: INVALIDATE STALE PROVENANCE — WATCHER REPORT")
    print("=" * 80)
    print(f"Target Asset URN:     {res.get('asset_urn')}")
    print(f"Decision ID:          {res.get('decision_id')}")
    print(f"Provenance Status:    {res.get('new_status', res.get('provenance_status', 'UNKNOWN')).upper()}")
    print(f"Written to DataHub:   {res.get('written_to_datahub')}")
    if res.get("stale_reason"):
        print(f"Staleness Reason:\n  {res.get('stale_reason')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
