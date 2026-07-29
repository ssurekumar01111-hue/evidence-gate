import json
from pathlib import Path
import pytest
from src.api.schemas import ChangeRequest
from src.discovery.parser import parse_change_request
from src.evidence.collector import build_evidence_bundle
from src.evidence.schemas import (
    EvidenceBundle,
    GlossaryTermRef,
    OwnerRef,
    DownstreamConsumer,
    AssertionRef,
)
from src.decision.risk_engine import evaluate_risk


# Milestone 1 discovery real glossary term URN for Revenue
REAL_REVENUE_GLOSSARY_URN = "urn:li:glossaryTerm:b2fd91.26e268c3-3688-4281-949e-8c1aa2600c02"


def test_schema_diff_parser_field_rename():
    """Step 1: Verify schema-diff parser for field_rename ChangeRequest payload."""
    fixture_path = Path("fixtures/net_revenue_rename.json")
    req = parse_change_request(fixture_path)

    assert req.change_id == "cr-net-revenue-001"
    assert req.change_type == "field_rename"
    assert req.source_asset == "urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details,PROD)"
    assert req.old_field == "order_total"
    assert req.new_field == "recognized_revenue"
    assert req.old_type == "decimal"
    assert req.new_type == "decimal"
    assert req.pr_url == "https://github.com/example/repo/pull/42"


def test_evidence_bundle_construction_from_datahub():
    """
    Step 2 & DoD item 1: Query live DataHub instance to produce a populated evidence bundle
    containing real owners, the Revenue glossary term, and downstream dashboard names.
    """
    req = parse_change_request("fixtures/net_revenue_rename.json")
    bundle = build_evidence_bundle(req)

    assert bundle.asset_urn == req.source_asset
    assert bundle.field_name == "order_total"

    # Check real owners pulled from DataHub
    owner_names = [o.name for o in bundle.asset_owners]
    assert "David Kim" in owner_names
    assert "Julia Novak" in owner_names

    # Check real glossary term URN from Milestone 1 discovery
    glossary_urns = [t.urn for t in bundle.all_glossary_terms]
    glossary_names = [t.name for t in bundle.all_glossary_terms]
    assert REAL_REVENUE_GLOSSARY_URN in glossary_urns
    assert "Revenue by Customer Class" in glossary_names

    # Check downstream BI consumer names pulled from DataHub
    consumer_names = [c.name for c in bundle.downstream_consumers]
    assert "Essential KPI Measures" in consumer_names or "ORDER_DETAILS" in consumer_names
    assert bundle.has_bi_consumer is True


def test_rule_revenue_glossary_term_linked():
    """Tests Decision Rules Table row: Field is linked to a glossary term such as Revenue."""
    req = ChangeRequest(
        change_id="test-rev-01",
        change_type="field_rename",
        source_asset="urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.tbl,PROD)",
        old_field="rev_col",
        new_field="new_rev_col",
        old_type="decimal",
        new_type="decimal",
        pr_url="https://github.com/example/repo/pull/1",
    )
    bundle = EvidenceBundle(
        asset_urn=req.source_asset,
        field_name=req.old_field,
        dataset_glossary_terms=[
            GlossaryTermRef(
                urn=REAL_REVENUE_GLOSSARY_URN,
                name="Revenue by Customer Class",
                description="Aggregated revenue metrics",
            )
        ],
        downstream_consumers=[
            DownstreamConsumer(
                urn="urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.etl_target,PROD)",
                name="etl_target",
                platform="snowflake",
            )
        ],
    )
    risk = evaluate_risk(req, bundle)

    assert "revenue_glossary_term_linked" in risk.signals_triggered
    assert risk.risk_score == 40  # +40 for revenue glossary term


def test_rule_downstream_bi_consumer():
    """Tests Decision Rules Table row: Field is in an executive dashboard lineage path."""
    req = ChangeRequest(
        change_id="test-bi-01",
        change_type="field_rename",
        source_asset="urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.tbl,PROD)",
        old_field="col_a",
        new_field="col_b",
        old_type="int",
        new_type="int",
        pr_url="https://github.com/example/repo/pull/1",
    )
    bundle = EvidenceBundle(
        asset_urn=req.source_asset,
        field_name=req.old_field,
        has_bi_consumer=True,
        downstream_consumers=[
            DownstreamConsumer(
                urn="urn:li:dataset:(urn:li:dataPlatform:powerbi,dash1,PROD)",
                name="Executive Summary Dashboard",
                platform="powerbi",
            )
        ],
    )
    risk = evaluate_risk(req, bundle)

    assert "downstream_bi_consumer_present" in risk.signals_triggered
    assert risk.risk_score == 35  # +35 for BI consumer


def test_rule_no_downstream_consumers_reduces_risk():
    """
    Tests Decision Rules Table row: No downstream consumers.
    SYNTHETIC INPUT COMMENT: Constructing a synthetic/mocked asset for this test case because all
    real showcase-ecommerce assets in DataHub have downstream consumers.
    """
    req = ChangeRequest(
        change_id="test-synth-no-consumer",
        change_type="field_rename",
        source_asset="urn:li:dataset:(urn:li:dataPlatform:snowflake,isolated_db.staging.orphan_table,PROD)",
        old_field="unused_col",
        new_field="renamed_unused_col",
        old_type="varchar",
        new_type="varchar",
        pr_url="https://github.com/example/repo/pull/99",
    )
    # Synthetic bundle with zero downstream consumers
    bundle = EvidenceBundle(
        asset_urn=req.source_asset,
        field_name=req.old_field,
        asset_owners=[OwnerRef(urn="urn:li:corpuser:alice", name="Alice Smith")],
        downstream_consumers=[],  # Zero consumers
        has_bi_consumer=False,
    )
    risk = evaluate_risk(req, bundle)

    assert "no_downstream_consumers" in risk.signals_triggered
    assert risk.risk_score == 0  # 0 - 20 clamped to 0
    assert risk.leaning == "approved"


def test_rule_incompatible_type_blocks():
    """Tests Decision Rules Table row: New field has incompatible type or semantic definition."""
    req = ChangeRequest(
        change_id="test-incompatible-type",
        change_type="field_rename",
        source_asset="urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.tbl,PROD)",
        old_field="amount",
        new_field="amount_str",
        old_type="decimal",
        new_type="varchar",  # Incompatible type change
        pr_url="https://github.com/example/repo/pull/1",
    )
    bundle = EvidenceBundle(asset_urn=req.source_asset, field_name=req.old_field)
    risk = evaluate_risk(req, bundle)

    assert "incompatible_field_type" in risk.signals_triggered
    assert risk.risk_score == 100
    assert risk.leaning == "blocked"


def test_rule_failing_quality_assertion_blocks():
    """Tests Decision Rules Table row: Existing quality assertion is failing."""
    req = ChangeRequest(
        change_id="test-failing-assertion",
        change_type="field_rename",
        source_asset="urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.tbl,PROD)",
        old_field="amount",
        new_field="net_amount",
        old_type="decimal",
        new_type="decimal",
        pr_url="https://github.com/example/repo/pull/1",
    )
    bundle = EvidenceBundle(
        asset_urn=req.source_asset,
        field_name=req.old_field,
        failing_assertions=[
            AssertionRef(
                urn="urn:li:assertion:failing-check-001",
                type="DATA_QUALITY",
                status="FAILED",
            )
        ],
    )
    risk = evaluate_risk(req, bundle)

    assert "failing_quality_assertion" in risk.signals_triggered
    assert risk.risk_score == 100
    assert risk.leaning == "blocked"


def test_rule_input_change_visibly_changes_risk_score():
    """
    DoD item 3: Assert that changing a rule input (removing the glossary link)
    visibly changes the computed risk score.
    """
    req = parse_change_request("fixtures/net_revenue_rename.json")
    
    # Bundle WITH revenue glossary term and BI consumer
    bundle_with_glossary = EvidenceBundle(
        asset_urn=req.source_asset,
        field_name=req.old_field,
        dataset_glossary_terms=[
            GlossaryTermRef(
                urn=REAL_REVENUE_GLOSSARY_URN,
                name="Revenue by Customer Class",
            )
        ],
        has_bi_consumer=True,
        downstream_consumers=[
            DownstreamConsumer(
                urn="urn:li:dataset:(urn:li:dataPlatform:powerbi,dash,PROD)",
                name="PowerBI Dash",
                platform="powerbi",
            )
        ],
    )
    risk_before = evaluate_risk(req, bundle_with_glossary)
    assert risk_before.risk_score == 75  # 35 (BI) + 40 (Glossary)
    assert "revenue_glossary_term_linked" in risk_before.signals_triggered

    # Bundle WITHOUT revenue glossary term (input changed)
    bundle_without_glossary = EvidenceBundle(
        asset_urn=req.source_asset,
        field_name=req.old_field,
        dataset_glossary_terms=[],  # Glossary term removed!
        has_bi_consumer=True,
        downstream_consumers=[
            DownstreamConsumer(
                urn="urn:li:dataset:(urn:li:dataPlatform:powerbi,dash,PROD)",
                name="PowerBI Dash",
                platform="powerbi",
            )
        ],
    )
    risk_after = evaluate_risk(req, bundle_without_glossary)
    
    # Assert risk score visibly changed
    assert risk_after.risk_score == 35  # Visibly dropped from 75 to 35
    assert "revenue_glossary_term_linked" not in risk_after.signals_triggered
    assert risk_after.risk_score != risk_before.risk_score


def test_end_to_end_milestone2_decision_path():
    """
    End-to-end Milestone 2 test running full pipeline on fixtures/net_revenue_rename.json
    against live DataHub instance.
    """
    req = parse_change_request("fixtures/net_revenue_rename.json")
    bundle = build_evidence_bundle(req)
    risk = evaluate_risk(req, bundle)

    assert risk.risk_score == 75
    assert risk.leaning == "needs-review"
    assert "downstream_bi_consumer_present" in risk.signals_triggered
    assert "revenue_glossary_term_linked" in risk.signals_triggered

    # Check real approver human names
    assert "David Kim" in risk.required_approvers
    assert "Julia Novak" in risk.required_approvers
    assert "Karen Okonkwo" in risk.required_approvers
