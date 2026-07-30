import os
import sys
from typing import List
from dotenv import load_dotenv
from google import genai

from src.api.schemas import ChangeRequest
from src.decision.schemas import RiskAssessment
from src.validation.schemas import RevenueValidationReport

# Automatically load environment variables from .env if present
load_dotenv()

# Consistent model configuration across the codebase
MODEL_NAME = "gemini-3.5-flash"

SIGNAL_HUMAN_NAMES = {
    "downstream_bi_consumer_present": "Field has real downstream BI/dashboard consumers",
    "revenue_glossary_term_linked": "Field is linked to critical Revenue glossary terms",
    "incompatible_field_type": "Field type changed between source and target",
    "failing_quality_assertion": "Existing data quality assertions are currently failing",
    "no_downstream_consumers": "No downstream consumers affected",
}

GLOBAL_FORBIDDEN_PHRASES = [
    "executive",
    "exec dashboard",
]

FORBIDDEN_PHRASES_BY_SIGNAL = {
    "incompatible_field_type": [
        "incompatible type",
        "incompatible field",
        "type mismatch",
        "type incompatibility",
        "type change",
        "type conversion",
        "differing type",
        "different type",
    ],
    "failing_quality_assertion": [
        "failing quality assertion",
        "assertion failure",
        "failing assertion",
        "quality assertion failure",
        "quality assertion failing",
        "quality assertion",
        "data quality check",
        "assertion check",
    ],
}


NO_DOWNSTREAM_HALLUCINATION_PHRASES = [
    "no downstream consumer",
    "no downstream consumers",
    "despite having no downstream",
    "having no downstream",
    "with no downstream",
    "without downstream",
    "no bi consumer",
    "no bi consumers",
    "no downstream dashboard",
    "no downstream dashboards",
]


def _build_fallback_rationale(
    change_request: ChangeRequest,
    risk_assessment: RiskAssessment,
    validation_report: RevenueValidationReport,
    final_status: str,
) -> str:
    """Computes the static template fallback business rationale."""
    if validation_report.result == "failed":
        return (
            f"Change BLOCKED: Field rename '{change_request.old_field}' -> '{change_request.new_field}' "
            f"causes a metric discrepancy. {validation_report.reason}"
        )
    elif risk_assessment.leaning == "blocked":
        return f"Change BLOCKED: {risk_assessment.rationale}"
    elif final_status == "needs-review":
        return f"Change NEEDS REVIEW: {risk_assessment.rationale}"
    else:
        return f"Change APPROVED: {risk_assessment.rationale}"


def _detect_hallucinated_signals(text: str, triggered_signals: List[str]) -> bool:
    """
    Returns True if generated text references signal categories that did NOT trigger
    or contains forbidden phrases such as 'executive' or contradicting downstream consumer facts.
    """
    text_lower = text.lower()
    for phrase in GLOBAL_FORBIDDEN_PHRASES:
        if phrase in text_lower:
            return True

    for signal_key, forbidden_phrases in FORBIDDEN_PHRASES_BY_SIGNAL.items():
        if signal_key not in triggered_signals:
            for phrase in forbidden_phrases:
                if phrase in text_lower:
                    return True

    if "downstream_bi_consumer_present" in triggered_signals:
        for phrase in NO_DOWNSTREAM_HALLUCINATION_PHRASES:
            if phrase in text_lower:
                return True

    return False


def generate_business_rationale(
    change_request: ChangeRequest,
    risk_assessment: RiskAssessment,
    validation_report: RevenueValidationReport,
    final_status: str,
    final_risk_score: int,
) -> str:
    """
    Generates a natural-language business rationale using Gemini LLM.
    Status and risk score are passed as FIXED, deterministic inputs.
    Strictly filters prompt facts to ONLY triggered risk signals and validates output against hallucinations.
    """
    fallback_rationale = _build_fallback_rationale(
        change_request, risk_assessment, validation_report, final_status
    )

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        warning_msg = (
            "[LLM_UNAVAILABLE] Falling back to template rationale — "
            "Gemini call failed: GEMINI_API_KEY environment variable is not set."
        )
        print(warning_msg, file=sys.stderr)
        return fallback_rationale

    # Construct list containing ONLY risk signals that actually triggered
    triggered_bullets = [
        f"  - {SIGNAL_HUMAN_NAMES.get(sig, sig)}"
        for sig in risk_assessment.signals_triggered
    ]
    signals_fact_text = (
        "\n".join(triggered_bullets)
        if triggered_bullets
        else "  - None (no risk signals triggered)"
    )

    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
You are Evidence Gate, an automated data governance and decision provenance engine.
Generate a concise, 2-3 sentence business rationale explaining an automated change request evaluation.

DETERMINISTIC EVALUATION FACTS (FIXED - DO NOT ALTER):
- Final Decision Status: {final_status.upper()}
- Numeric Risk Score: {final_risk_score}/100
- Field Transition: '{change_request.old_field}' ({change_request.old_type}) -> '{change_request.new_field}' ({change_request.new_type})
- Source Asset URN: {change_request.source_asset}
- Triggered Risk Signals (ONLY THESE SIGNALS FIRED):
{signals_fact_text}
- Revenue Metric Validation Result: {validation_report.result.upper()}
- Metric Aggregate Shift (Delta): {validation_report.delta_pct:.2f}% (Allowed Tolerance: {validation_report.tolerance_pct:.2f}%)
- Validation Details: {validation_report.reason}

INSTRUCTIONS:
1. Explain the business rationale for this decision in 2-3 clear, professional sentences based STRICTLY on the deterministic facts above.
2. Include the exact decision status ({final_status.upper()}), risk score ({final_risk_score}/100), and metric delta percentage ({validation_report.delta_pct:.2f}%).
3. Only reference the signals listed above under 'Triggered Risk Signals'. Do not infer, assume, or mention any risk factor, signal, or reason not explicitly provided in the facts (such as type incompatibility or failing quality assertions), even if it seems plausible for a blocked change. Note that field types match ('{change_request.old_type}' to '{change_request.new_type}') and no quality assertions failed. If 'Field has real downstream BI/dashboard consumers' is listed in Triggered Risk Signals, do NOT claim or imply there are no downstream consumers affected. Do not use the word 'executive' or label any dashboard as 'executive'.
4. Respond with ONLY the business rationale text.
"""
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        text = response.text.strip() if response and response.text else ""
        if not text:
            raise ValueError("Gemini returned empty response text.")

        # Post-generation safety validation: check for hallucinated non-triggered signals
        if _detect_hallucinated_signals(text, risk_assessment.signals_triggered):
            warning_msg = (
                "[LLM_HALLUCINATION_DETECTED] Gemini output referenced signals not present "
                "in input facts — falling back to template."
            )
            print(warning_msg, file=sys.stderr)
            return fallback_rationale

        return text
    except Exception as e:
        warning_msg = (
            f"[LLM_UNAVAILABLE] Falling back to template rationale — Gemini call failed: {e}"
        )
        print(warning_msg, file=sys.stderr)
        return fallback_rationale
