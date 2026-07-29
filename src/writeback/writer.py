import os
from datetime import datetime
from typing import Dict, Any, Optional
from datahub.ingestion.graph.client import DataHubGraph, DataHubGraphConfig
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import (
    DatasetPropertiesClass,
    InstitutionalMemoryClass,
    InstitutionalMemoryMetadataClass,
    AuditStampClass,
)
from src.api.schemas import DecisionReceipt


def write_decision_provenance(
    receipt: DecisionReceipt, gms_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Writes Decision Provenance structured metadata back to the target DataHub asset(s):
    1. Custom Properties (DatasetPropertiesClass): decision ID, status, risk score, rationale, validation, approvers, revalidate expiry, invalidation inputs.
    2. Documentation Link (InstitutionalMemoryClass): PR URL and summary link.
    3. Native Incident (raiseIncident mutation): Raised if decision status is 'blocked'.
    """
    target_gms_url = gms_url or os.getenv("DATAHUB_GMS_URL", "http://localhost:8080")
    graph = DataHubGraph(DataHubGraphConfig(server=target_gms_url))

    asset_urn = receipt.affected_assets[0]

    # 1. Prepare custom properties payload
    custom_props = {
        "eg_decision_id": receipt.decision_id,
        "eg_status": receipt.status,
        "eg_provenance_status": "active",
        "eg_risk_score": str(receipt.risk_score),
        "eg_business_rationale": receipt.business_rationale,
        "eg_validation_result": receipt.validation.result,
        "eg_validation_reason": receipt.validation.reason,
        "eg_required_approvers": ", ".join(receipt.required_approvers),
        "eg_recommended_action": receipt.recommended_action,
        "eg_revalidate_after": receipt.revalidate_after,
        "eg_invalidation_inputs": ", ".join(receipt.invalidation_inputs),
        "eg_graph_snapshot_at": receipt.graph_snapshot_at,
        "eg_change_url": receipt.change_url,
    }

    # Fetch existing properties to preserve asset name
    existing_res = graph.execute_graphql(
        """
        query getAssetName($urn: String!) {
          dataset(urn: $urn) {
            properties {
              name
            }
          }
        }
        """,
        variables={"urn": asset_urn},
    )
    asset_name = (
        existing_res.get("dataset", {}).get("properties", {}).get("name")
        or "ORDER_DETAILS"
    )

    # Emit DatasetProperties aspect with Decision Provenance custom properties
    props_mcp = MetadataChangeProposalWrapper(
        entityUrn=asset_urn,
        aspect=DatasetPropertiesClass(
            name=asset_name,
            customProperties=custom_props,
        ),
    )
    graph.emit_mcp(props_mcp)

    # 2. Emit Documentation link (InstitutionalMemoryClass)
    now_ms = int(datetime.now().timestamp() * 1000)
    memory_mcp = MetadataChangeProposalWrapper(
        entityUrn=asset_urn,
        aspect=InstitutionalMemoryClass(
            elements=[
                InstitutionalMemoryMetadataClass(
                    url=receipt.change_url,
                    description=f"[Evidence Gate Provenance {receipt.decision_id}] Status: {receipt.status.upper()} (Risk Score {receipt.risk_score}). Rationale: {receipt.business_rationale[:120]}...",
                    createStamp=AuditStampClass(
                        time=now_ms, actor="urn:li:corpuser:datahub"
                    ),
                )
            ]
        ),
    )
    graph.emit_mcp(memory_mcp)

    incident_urn = None
    # 3. If decision is blocked, raise a native DataHub Incident
    if receipt.status == "blocked":
        mutation = """
        mutation raiseInc($input: RaiseIncidentInput!) {
          raiseIncident(input: $input)
        }
        """
        variables = {
            "input": {
                "type": "OPERATIONAL",
                "resourceUrn": asset_urn,
                "title": f"[Evidence Gate] Schema Change Blocked ({receipt.decision_id})",
                "description": f"{receipt.business_rationale} Required approvers: {', '.join(receipt.required_approvers)}.",
            }
        }
        try:
            inc_res = graph.execute_graphql(mutation, variables=variables)
            incident_urn = inc_res.get("raiseIncident")
        except Exception as e:
            incident_urn = f"error: {str(e)}"

    return {
        "asset_urn": asset_urn,
        "decision_id": receipt.decision_id,
        "status": receipt.status,
        "custom_properties_emitted": len(custom_props),
        "documentation_link": receipt.change_url,
        "incident_urn": incident_urn,
    }
