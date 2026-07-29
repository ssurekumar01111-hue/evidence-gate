import os
from typing import Optional, List
from datahub.ingestion.graph.client import DataHubGraph, DataHubGraphConfig
from src.api.schemas import ChangeRequest
from src.evidence.schemas import (
    EvidenceBundle,
    GlossaryTermRef,
    OwnerRef,
    DownstreamConsumer,
    AssertionRef,
)


GET_DATASET_EVIDENCE_QUERY = """
query getDatasetEvidence($urn: String!) {
  dataset(urn: $urn) {
    urn
    name
    platform {
      name
    }
    schemaMetadata {
      fields {
        fieldPath
        type
        nativeDataType
        description
        glossaryTerms {
          terms {
            term {
              urn
              properties {
                name
                description
              }
            }
          }
        }
      }
    }
    glossaryTerms {
      terms {
        term {
          urn
          properties {
            name
            description
          }
        }
      }
    }
    ownership {
      owners {
        owner {
          ... on CorpUser {
            urn
            username
            properties {
              displayName
              email
            }
          }
          ... on CorpGroup {
            urn
            name
          }
        }
        type
      }
    }
    assertions {
      total
      assertions {
        urn
        type
        info {
          type
        }
      }
    }
    downstream: lineage(input: {direction: DOWNSTREAM}) {
      relationships {
        type
        entity {
          urn
          type
          ... on Dataset {
            name
            platform {
              name
            }
            ownership {
              owners {
                owner {
                  ... on CorpUser {
                    urn
                    username
                    properties {
                      displayName
                    }
                  }
                  ... on CorpGroup {
                    urn
                    name
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

BI_PLATFORMS = {"powerbi", "tableau", "looker", "metabase", "superset", "mode", "thoughtspot", "grafana", "quicksight"}


def _extract_owner_ref(owner_dict: dict) -> Optional[OwnerRef]:
    if not owner_dict or "owner" not in owner_dict:
        return None
    o = owner_dict["owner"]
    urn = o.get("urn", "")
    props = o.get("properties") or {}
    display_name = props.get("displayName") or o.get("name") or o.get("username") or urn
    return OwnerRef(urn=urn, name=display_name, type=owner_dict.get("type"))


def build_evidence_bundle(
    change_request: ChangeRequest, gms_url: Optional[str] = None
) -> EvidenceBundle:
    """
    Queries DataHub live GMS endpoint via Agent Context Kit pattern to assemble a bounded,
    task-specific EvidenceBundle for the given ChangeRequest asset and field.
    """
    target_gms_url = gms_url or os.getenv("DATAHUB_GMS_URL", "http://localhost:8080")
    graph = DataHubGraph(DataHubGraphConfig(server=target_gms_url))

    res = graph.execute_graphql(GET_DATASET_EVIDENCE_QUERY, variables={"urn": change_request.source_asset})
    dataset_data = res.get("dataset") if res else None

    if not dataset_data:
        # Fallback if asset is missing or not found in DataHub
        return EvidenceBundle(
            asset_urn=change_request.source_asset,
            field_name=change_request.old_field,
        )

    # 1. Parse field-level glossary terms for the affected field
    field_glossary_terms: List[GlossaryTermRef] = []
    schema_meta = dataset_data.get("schemaMetadata") or {}
    for f in schema_meta.get("fields", []):
        if f.get("fieldPath") == change_request.old_field:
            gt_container = f.get("glossaryTerms") or {}
            for t_item in gt_container.get("terms", []):
                t_obj = t_item.get("term") or {}
                t_urn = t_obj.get("urn")
                t_props = t_obj.get("properties") or {}
                if t_urn:
                    field_glossary_terms.append(
                        GlossaryTermRef(
                            urn=t_urn,
                            name=t_props.get("name") or t_urn,
                            description=t_props.get("description"),
                        )
                    )

    # 2. Parse dataset-level glossary terms
    dataset_glossary_terms: List[GlossaryTermRef] = []
    ds_gt_container = dataset_data.get("glossaryTerms") or {}
    for t_item in ds_gt_container.get("terms", []):
        t_obj = t_item.get("term") or {}
        t_urn = t_obj.get("urn")
        t_props = t_obj.get("properties") or {}
        if t_urn:
            dataset_glossary_terms.append(
                GlossaryTermRef(
                    urn=t_urn,
                    name=t_props.get("name") or t_urn,
                    description=t_props.get("description"),
                )
            )

    # 3. Parse asset owners
    asset_owners: List[OwnerRef] = []
    ownership = dataset_data.get("ownership") or {}
    for o_entry in ownership.get("owners", []):
        ref = _extract_owner_ref(o_entry)
        if ref:
            asset_owners.append(ref)

    # 4. Parse downstream lineage for BI consumers and their owners
    downstream_consumers: List[DownstreamConsumer] = []
    has_bi = False
    downstream_container = dataset_data.get("downstream") or {}
    for rel in downstream_container.get("relationships", []):
        entity = rel.get("entity") or {}
        platform_info = entity.get("platform") or {}
        platform_name = (platform_info.get("name") or "").lower()
        ent_urn = entity.get("urn", "")
        ent_name = entity.get("name") or ent_urn

        # Check if platform is a known BI platform or platform name is in URN
        is_bi = platform_name in BI_PLATFORMS or any(p in ent_urn.lower() for p in BI_PLATFORMS)
        if is_bi:
            has_bi = True

        consumer_owners: List[OwnerRef] = []
        ent_ownership = entity.get("ownership") or {}
        for o_entry in ent_ownership.get("owners", []):
            ref = _extract_owner_ref(o_entry)
            if ref:
                consumer_owners.append(ref)

        downstream_consumers.append(
            DownstreamConsumer(
                urn=ent_urn,
                name=ent_name,
                platform=platform_name or "unknown",
                owners=consumer_owners,
            )
        )

    # 5. Parse quality assertions
    failing_assertions: List[AssertionRef] = []
    assertions_meta = dataset_data.get("assertions") or {}
    for ass_item in assertions_meta.get("assertions", []):
        # Check if assertion has failing status
        status = ass_item.get("status", "UNKNOWN")
        if status == "FAILED":
            failing_assertions.append(
                AssertionRef(
                    urn=ass_item.get("urn", ""),
                    type=ass_item.get("type", "UNKNOWN"),
                    status=status,
                )
            )

    return EvidenceBundle(
        asset_urn=change_request.source_asset,
        field_name=change_request.old_field,
        field_glossary_terms=field_glossary_terms,
        dataset_glossary_terms=dataset_glossary_terms,
        asset_owners=asset_owners,
        downstream_consumers=downstream_consumers,
        has_bi_consumer=has_bi,
        failing_assertions=failing_assertions,
    )
