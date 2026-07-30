import os
import sys
import json
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
from google import genai
from datahub.ingestion.graph.client import DataHubGraph, DataHubGraphConfig
from src.api.schemas import ChangeRequest

load_dotenv()


def narrate_precedent_comparison(
    applies_list: List[str],
    differs_list: List[str],
    candidate_id: str,
    prior_id: str,
) -> Tuple[List[str], List[str]]:
    """
    Uses Gemini LLM to naturally rephrase deterministic precedent comparison facts.
    Falls back to deterministic template lists if GEMINI_API_KEY is missing or API call fails.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        warning_msg = (
            "[LLM_UNAVAILABLE] Falling back to template precedent comparison — "
            "Gemini call failed: GEMINI_API_KEY environment variable is not set."
        )
        print(warning_msg, file=sys.stderr)
        return applies_list, differs_list

    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
You are Evidence Gate, an automated data governance engine.
Rephrase these deterministic precedent comparison facts between candidate Change Request '{candidate_id}' and prior decision '{prior_id}'.

DETERMINISTIC FACTS (FIXED - DO NOT ALTER OR OMIT):
What Still Applies:
{json.dumps(applies_list, indent=2)}

What Differs:
{json.dumps(differs_list, indent=2)}

INSTRUCTIONS:
1. Rephrase the bullet points under 'What Still Applies' and 'What Differs' into professional, natural language sentences.
2. Return a valid JSON object with EXACTLY two keys: "what_still_applies" (list of strings) and "what_differs" (list of strings).
3. Do not add, remove, or change any underlying facts or decision outcomes.
4. Do not use the word 'executive' or label any dashboard as 'executive'.
"""
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
        )
        text = response.text.strip() if response and response.text else ""
        if text.startswith("```json"):
            text = text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif text.startswith("```"):
            text = text.split("```", 1)[1].split("```", 1)[0].strip()

        parsed = json.loads(text)
        new_applies = parsed.get("what_still_applies", applies_list)
        new_differs = parsed.get("what_differs", differs_list)
        if isinstance(new_applies, list) and isinstance(new_differs, list):
            for item in new_applies + new_differs:
                item_lower = str(item).lower()
                if "executive" in item_lower or "exec dashboard" in item_lower:
                    warning_msg = (
                        "[LLM_HALLUCINATION_DETECTED] Gemini precedent comparison output referenced forbidden phrase 'executive' — falling back to template."
                    )
                    print(warning_msg, file=sys.stderr)
                    return applies_list, differs_list
            return new_applies, new_differs
        else:
            raise ValueError("Invalid JSON structure returned by Gemini")
    except Exception as e:
        warning_msg = (
            f"[LLM_UNAVAILABLE] Falling back to template precedent comparison — Gemini call failed: {e}"
        )
        print(warning_msg, file=sys.stderr)
        return applies_list, differs_list


def find_precedent_decisions(
    change_request: ChangeRequest, gms_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Precedent Retrieval Engine: Searches DataHub live graph for prior Decision Provenance artifacts,
    reuses relevant evidence, and produces an explicit 'What Still Applies / What Differs' comparison.
    """
    target_gms_url = gms_url or os.getenv("DATAHUB_GMS_URL", "http://localhost:8080")
    graph = DataHubGraph(DataHubGraphConfig(server=target_gms_url))

    # Search for all datasets in DataHub that contain custom properties
    query = """
    query searchPrecedents {
      search(input: {type: DATASET, query: "*", count: 20}) {
        searchResults {
          entity {
            urn
            ... on Dataset {
              name
              properties {
                customProperties {
                  key
                  value
                }
              }
            }
          }
        }
      }
    }
    """

    res = graph.execute_graphql(query)
    results = (
        res.get("search", {}).get("searchResults", []) if res else []
    )

    found_precedents: List[Dict[str, Any]] = []

    for item in results:
        entity = item.get("entity") or {}
        props = (entity.get("properties") or {}).get("customProperties") or []
        props_map = {p["key"]: p["value"] for p in props}

        if "eg_decision_id" in props_map:
            prior_id = props_map.get("eg_decision_id")
            prior_asset = entity.get("urn")
            prior_status = props_map.get("eg_status")
            prior_risk = props_map.get("eg_risk_score")
            prior_rationale = props_map.get("eg_business_rationale")
            prior_url = props_map.get("eg_change_url")

            # Determine comparison specifics
            applies_list = []
            differs_list = []

            # 1. Semantic gap check
            if (
                change_request.old_field == "order_total"
                and change_request.new_field == "recognized_revenue"
            ):
                applies_list.append(
                    "Identical field rename semantic gap: gross transaction metric ('order_total') -> net metric ('recognized_revenue')."
                )
                applies_list.append(
                    "Revenue glossary term definition & aggregate discrepancy threshold (1.00%) applies."
                )

            # 2. Asset comparison
            if prior_asset == change_request.source_asset:
                applies_list.append("Same target asset URN and dataset lineage path.")
            else:
                differs_list.append(
                    f"Different target asset: candidate is '{change_request.source_asset}' vs prior '{prior_asset}'."
                )

            # 3. Change ID & PR URL comparison
            differs_list.append(
                f"Change Request ID: '{change_request.change_id}' vs prior '{prior_id}'."
            )
            if prior_url != change_request.pr_url:
                differs_list.append(
                    f"Pull Request URL: '{change_request.pr_url}' vs prior '{prior_url}'."
                )

            # Use LLM narrator with fallback for precedent comparison phrasing
            applies_list, differs_list = narrate_precedent_comparison(
                applies_list, differs_list, change_request.change_id, prior_id
            )

            found_precedents.append(
                {
                    "precedent_decision_id": prior_id,
                    "prior_asset_urn": prior_asset,
                    "prior_status": prior_status,
                    "prior_risk_score": prior_risk,
                    "prior_rationale": prior_rationale,
                    "what_still_applies": applies_list,
                    "what_differs": differs_list,
                    "reused_evidence": [
                        "Revenue glossary term definition",
                        "Gross-to-net tax & status exclusion query pattern",
                        "1.00% validation tolerance threshold",
                    ],
                }
            )

    return {
        "candidate_change_id": change_request.change_id,
        "candidate_source_asset": change_request.source_asset,
        "precedents_found_count": len(found_precedents),
        "precedents": found_precedents,
    }
