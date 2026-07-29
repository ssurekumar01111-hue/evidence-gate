from fastapi import FastAPI, HTTPException
from src.api.schemas import ChangeRequest, DecisionReceipt
from src.evidence.collector import build_evidence_bundle
from src.decision.risk_engine import evaluate_risk
from src.validation.engine import validate_revenue_compatibility
from src.decision.evaluator import build_decision_receipt
from src.writeback.writer import write_decision_provenance

app = FastAPI(
    title="Evidence Gate API",
    description="Operational Decision Provenance Engine for DataHub",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "evidence-gate"}


@app.post("/evaluate", response_model=DecisionReceipt)
@app.post("/api/evaluate", response_model=DecisionReceipt)
def evaluate_change(request: ChangeRequest) -> DecisionReceipt:
    try:
        evidence = build_evidence_bundle(request)
        risk = evaluate_risk(request, evidence)
        val = validate_revenue_compatibility()
        receipt = build_decision_receipt(request, evidence, risk, val)
        write_decision_provenance(receipt)
        return receipt
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
