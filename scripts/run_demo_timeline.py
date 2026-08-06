#!/usr/bin/env python3
"""
Evidence Gate — Complete End-to-End Demo Script Runner
Executes the full timeline start-to-finish against live DataHub GMS:
1. Discover graph context via Agent Context Kit pattern.
2. Evaluate Milestone 2 risk rules (75 / needs-review).
3. Execute Milestone 3 DuckDB metric validation (13.16% shift -> BLOCKED).
4. Generate dbt compatibility patch & migration test file into examples/.
5. Write Decision Provenance artifact back to DataHub (properties, links, incident).
6. Independent Retrieval: Read stored provenance from DataHub from a fresh query.
7. Graph-Change Watcher: Simulate real graph change (remove glossary term) & flip status to STALE on DataHub.
8. Precedent Retrieval: Process 2nd ChangeRequest on order_details_replica with explicit comparison.
"""
import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.api.schemas import ChangeRequest
from src.discovery.parser import parse_change_request
from src.evidence.collector import build_evidence_bundle
from src.decision.risk_engine import evaluate_risk
from src.validation.engine import validate_revenue_compatibility
from src.remediation.patch_generator import generate_remediation_artifacts
from src.decision.evaluator import build_decision_receipt
from src.writeback.writer import write_decision_provenance
from src.writeback.retriever import retrieve_decision_provenance
from src.invalidation.watcher import (
    simulate_graph_change,
    check_and_invalidate_provenance,
    restore_glossary_terms,
)
from src.precedent.retriever import find_precedent_decisions


def run_full_demo():
    print("=" * 80)
    print("      DATAHUB ORGANIZATIONAL REASONING — EVIDENCE GATE DEMO PIPELINE")
    print("=" * 80)

    # ---------------------------------------------------------
    # STEP 1: Parse Change Request & Discover Live Graph Context
    # ---------------------------------------------------------
    print("\n[STEP 1] PARSING CHANGE REQUEST & DISCOVERING DATAHUB CONTEXT...")
    req1 = parse_change_request("fixtures/net_revenue_rename.json")
    print(f"  Change ID:      {req1.change_id}")
    print(f"  Source Asset:   {req1.source_asset}")
    print(f"  Field Rename:   '{req1.old_field}' -> '{req1.new_field}' ({req1.old_type} -> {req1.new_type})")
    print(f"  Pull Request:   {req1.pr_url}")

    bundle1 = build_evidence_bundle(req1)
    print(f"  Owners:         {[o.name for o in bundle1.asset_owners]}")
    print(f"  Glossary Terms: {[t.name for t in bundle1.all_glossary_terms]}")
    print(f"  BI Consumers:   {len(bundle1.downstream_consumers)} assets (PowerBI, Looker, Tableau)")

    # ---------------------------------------------------------
    # STEP 2: Evaluate Milestone 2 Risk Rules
    # ---------------------------------------------------------
    print("\n[STEP 2] EVALUATING DETERMINISTIC RISK RULES (MILESTONE 2)...")
    risk1 = evaluate_risk(req1, bundle1)
    print(f"  Risk Score:     {risk1.risk_score}/100")
    print(f"  Leaning:        {risk1.leaning.upper()}")
    print(f"  Signals:        {risk1.signals_triggered}")
    print(f"  Approvers:      {risk1.required_approvers}")

    # ---------------------------------------------------------
    # STEP 3: Execute Milestone 3 DuckDB Metric Validation
    # ---------------------------------------------------------
    print("\n[STEP 3] RUNNING READ-ONLY DUCKDB METRIC VALIDATION (MILESTONE 3)...")
    val1 = validate_revenue_compatibility()
    print(f"  Validation:     {val1.result.upper()}")
    print(f"  Old Aggregate:  ${val1.old_aggregate:,.2f}")
    print(f"  Proposed Agg:   ${val1.proposed_aggregate:,.2f}")
    print(f"  Numeric Delta:  {val1.delta_pct:.2f}% (Tolerance: {val1.tolerance_pct:.2f}%)")

    # ---------------------------------------------------------
    # STEP 4: Build DecisionReceipt & Generate Remediation Patch
    # ---------------------------------------------------------
    print("\n[STEP 4] COMBINING RISK + VALIDATION & GENERATING REMEDIATION PATCH...")
    receipt1 = build_decision_receipt(req1, bundle1, risk1, val1, decision_id="eg-2026-001")
    patch_path, test_path = generate_remediation_artifacts(req1, val1)
    print(f"  Final Status:   {receipt1.status.upper()}")
    print(f"  Final Risk:     {receipt1.risk_score}/100")
    print(f"  Patch Saved:    {patch_path}")
    print(f"  Test Saved:     {test_path}")

    # ---------------------------------------------------------
    # STEP 5: Write Decision Provenance Back to DataHub GMS
    # ---------------------------------------------------------
    print("\n[STEP 5] WRITING DECISION PROVENANCE BACK TO DATAHUB GMS...")
    wb_res = write_decision_provenance(receipt1)
    print(f"  Target Asset:   {wb_res['asset_urn']}")
    print(f"  Properties:     {wb_res['custom_properties_emitted']} custom properties emitted")
    print(f"  Doc Link:       {wb_res['documentation_link']}")
    print(f"  Incident URN:   {wb_res['incident_urn']}")

    # ---------------------------------------------------------
    # STEP 6: Independent Decision Retrieval Test
    # ---------------------------------------------------------
    print("\n[STEP 6] INDEPENDENT DECISION RETRIEVAL (FRESH DATAHUB QUERY)...")
    retrieved = retrieve_decision_provenance(req1.source_asset)
    print(f"  Retrieved ID:   {retrieved.get('decision_id')}")
    print(f"  Outcome:        {retrieved.get('status').upper()}")
    print(f"  Proven. Status: {retrieved.get('provenance_status').upper()}")
    print(f"  Stored Reason:  {retrieved.get('validation_reason')}")

    # ---------------------------------------------------------
    # STEP 7: Simulate Graph Change & Invalidate Provenance
    # ---------------------------------------------------------
    print("\n[STEP 7] GRAPH-CHANGE WATCHER: SIMULATING GRAPH DEPENDENCY CHANGE...")
    sim_res = simulate_graph_change(req1.source_asset, action="remove_glossary_term")
    print(f"  Graph Action:   Removed Glossary Term ({sim_res['removed_term_urn']})")

    inv_res = check_and_invalidate_provenance(req1.source_asset)
    print(f"  Watcher Result: Provenance Status flipped to '{inv_res['new_status'].upper()}' on DataHub!")
    print(f"  Stale Reason:   {inv_res['stale_reason']}")

    # Confirm staleness from a fresh DataHub read
    retrieved_stale = retrieve_decision_provenance(req1.source_asset)
    print(f"  Fresh GMS Read: eg_provenance_status = '{retrieved_stale.get('provenance_status')}'")

    # ---------------------------------------------------------
    # STEP 8: Precedent Retrieval for Second Similar Change
    # ---------------------------------------------------------
    print("\n[STEP 8] PRECEDENT RETRIEVAL FOR SECOND SIMILAR CHANGE REQUEST...")
    req2 = ChangeRequest(
        change_id="cr-order-history-002",
        change_type="field_rename",
        source_asset="urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details_replica,PROD)",
        old_field="order_total",
        new_field="recognized_revenue",
        old_type="decimal",
        new_type="decimal",
        pr_url="https://github.com/example/repo/pull/105",
    )
    prec_res = find_precedent_decisions(req2)
    print(f"  Precedents Found: {prec_res['precedents_found_count']}")
    for p in prec_res["precedents"]:
        print(f"  Precedent ID:     {p['precedent_decision_id']} (Prior Status: {p['prior_status'].upper()})")
        print("  What Still Applies:")
        for item in p["what_still_applies"]:
            print(f"    - {item}")
        print("  What Differs:")
        for item in p["what_differs"]:
            print(f"    - {item}")

    print("\n" + "=" * 80)
    print("      EVIDENCE GATE DEMO PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_full_demo()
