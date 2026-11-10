"""
API Endpoints: Multi-Agent Analysis and Decision (F06, F07, F09, F12).
Executes the multi-agent workflow, retrieves agent findings, citations, and provisional decision.
"""

from typing import Dict, Any, List
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.case import Case, AgentRun, AuditEvent, Document
from app.orchestrator.graph import execute_underwriting_workflow

router = APIRouter(prefix="/cases/{case_id}", tags=["Analysis & Multi-Agents"])


@router.post("/analyze")
def trigger_analysis(case_id: str, db: Session = Depends(get_db)):
    """
    Triggers the Multi-Agent Underwriting Workflow:
    - Runs all 6 specialized agents
    - Evaluates actuarial GLM and XGBoost models
    - Cross-checks documents and contradictions
    - Consolidates provisional recommendation
    - Persists AgentRuns and updates Case status
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    # 1. Reconstruct full case context from raw input + documents
    context = json.loads(case.raw_input_json) if case.raw_input_json else {}
    context["case_id"] = case_id
    context["coverage_requested"] = case.coverage_requested

    # Merge extracted fields from uploaded documents if available
    docs = db.query(Document).filter(Document.case_id == case_id).all()
    for d in docs:
        if d.extracted_fields_json:
            fields = json.loads(d.extracted_fields_json)
            for f in fields:
                fname = f["field_name"]
                fval = f["value"]
                if fname in ["bonus_malus", "prior_claims_count"]:
                    context.setdefault("claims_summary", {})[fname] = fval
                elif fname in ["vehicle_power", "vehicle_model", "license_plate"]:
                    context.setdefault("vehicle", {})[fname] = fval
                elif fname in ["driver_age", "licence_years", "usage"]:
                    context.setdefault("applicant", {})[fname] = fval

    # 2. Execute Orchestrated Multi-Agent Workflow
    result = execute_underwriting_workflow(context)

    # 3. Clear previous runs and persist new AgentRun records
    db.query(AgentRun).filter(AgentRun.case_id == case_id).delete()

    agent_outputs = result.get("agent_outputs", {})
    for agent_id, out in agent_outputs.items():
        run_record = AgentRun(
            id=f"RUN-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}",
            case_id=case_id,
            agent_id=agent_id,
            agent_name=out.get("agent_name", agent_id),
            version=out.get("version", "1.0.0"),
            status=out.get("status", "SUCCESS"),
            confidence_score=out.get("confidence_score", 1.0),
            findings_json=json.dumps(out.get("findings", [])),
            alerts_json=json.dumps(out.get("alerts", [])),
            evidence_json=json.dumps(out.get("evidence", [])),
            sources_json=json.dumps(out.get("sources", [])),
            missing_fields_json=json.dumps(out.get("missing_fields", []))
        )
        db.add(run_record)

    # 4. Update Case status and provisional decision
    prov_dec = result.get("provisional_decision", {})
    risk_out = agent_outputs.get("AGENT_03_RISK_ASSESSMENT", {})
    act_calc = risk_out.get("metadata", {}).get("actuarial_calculation", {})

    case.status = "UNDER_REVIEW"
    case.decision_code = prov_dec.get("decision_code")
    case.provisional_recommendation = prov_dec.get("provisional_recommendation")
    case.risk_tier = act_calc.get("risk_tier", "MODERATE")
    case.pure_premium_eur = act_calc.get("pure_premium_eur")
    case.updated_at = datetime.utcnow()

    # 5. Cryptographic Audit Event
    last_audit = db.query(AuditEvent).filter(AuditEvent.case_id == case_id).order_by(AuditEvent.timestamp.desc()).first()
    prev_hash = last_audit.current_hash if last_audit else ""
    audit = AuditEvent.create_event(
        case_id=case_id,
        event_type="ANALYSIS_EXECUTED",
        actor="LangGraph Orchestrator",
        details={
            "agents_executed": list(agent_outputs.keys()),
            "decision_code": case.decision_code,
            "pure_premium_eur": case.pure_premium_eur,
            "risk_tier": case.risk_tier,
            "contradictions_count": len(result.get("contradictions", []))
        },
        prev_hash=prev_hash
    )
    db.add(audit)
    db.commit()

    return result


@router.get("/status")
def get_case_status(case_id: str, db: Session = Depends(get_db)):
    """
    Returns case processing status and execution summary.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    runs = db.query(AgentRun).filter(AgentRun.case_id == case_id).all()

    return {
        "case_id": case.id,
        "status": case.status,
        "decision_code": case.decision_code,
        "risk_tier": case.risk_tier,
        "agents_completed": len(runs),
        "updated_at": case.updated_at.isoformat() if case.updated_at else None
    }


@router.get("/findings")
def get_case_findings(case_id: str, db: Session = Depends(get_db)):
    """
    Returns structured findings, evidence, and citations of all 6 agents.
    """
    runs = db.query(AgentRun).filter(AgentRun.case_id == case_id).all()
    if not runs:
        raise HTTPException(status_code=404, detail="No agent runs found. Run /analyze first.")
    return [r.to_dict() for r in runs]


@router.get("/decision")
def get_case_decision(case_id: str, db: Session = Depends(get_db)):
    """
    Returns consolidated provisional decision and matrix dimensions.
    Uses the stored decision from the analysis to ensure consistency.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    # Get agent runs to extract decision dimensions
    runs = db.query(AgentRun).filter(AgentRun.case_id == case_id).all()
    agent_outputs = {r.agent_id: r.to_dict() for r in runs}

    # Use stored decision if available, otherwise re-evaluate
    if case.decision_code:
        # Extract risk tier and premium from stored values
        risk_tier = case.risk_tier or "MODERATE"
        pure_premium = case.pure_premium_eur or 0.0

        # Get decision details from the risk assessment agent
        risk_run = next((r for r in runs if r.agent_id == "AGENT_03_RISK_ASSESSMENT"), None)
        if risk_run and risk_run.findings_json:
            findings = json.loads(risk_run.findings_json)
            # Extract factors from findings
            favorable_factors = []
            unfavorable_factors = []
            for finding in findings:
                if "Charge pure technique" in finding or "Fréquence" in finding:
                    unfavorable_factors.append(finding)
                elif "conforme" in finding.lower() or "standard" in finding.lower():
                    favorable_factors.append(finding)

            # Get uncertainty from risk agent findings (simplified)
            uncertainty_level = "LOW"
            # For now, use a simple heuristic based on risk tier
            if risk_tier in ["HIGH", "CRITICAL"]:
                uncertainty_level = "HIGH"
            elif risk_tier == "MODERATE":
                uncertainty_level = "MEDIUM"

            return {
                "decision_code": case.decision_code,
                "risk_tier": risk_tier,
                "pure_premium_estimate": pure_premium,
                "confidence_level": 0.85,
                "favorable_factors": favorable_factors,
                "unfavorable_factors": unfavorable_factors,
                "required_actions": [],
                "justification": case.provisional_recommendation or "",
                "dimensions": {
                    "actuarial_risk_level": risk_tier,
                    "data_quality": "COMPLETE",
                    "model_uncertainty": uncertainty_level
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    # Fallback: re-evaluate if no stored decision
    context = json.loads(case.raw_input_json) if case.raw_input_json else {}
    from app.orchestrator.decision_engine import DeterministicDecisionEngine
    decision = DeterministicDecisionEngine.evaluate(agent_outputs, context)

    # Format for frontend
    return {
        "decision_code": decision.get("decision_code", case.decision_code or "PROCEED_STANDARD"),
        "risk_tier": decision.get("risk_tier", case.risk_tier or "MODERATE"),
        "pure_premium_estimate": case.pure_premium_eur or decision.get("pure_premium_eur", 0),
        "confidence_level": decision.get("confidence_level", 0.85),
        "favorable_factors": decision.get("favorable_factors", []),
        "unfavorable_factors": decision.get("unfavorable_factors", []),
        "required_actions": decision.get("required_actions", []),
        "justification": decision.get("justification", ""),
        "dimensions": decision.get("dimensions", {
            "risk": {"score": 0.5, "label": "Modéré", "details": ""},
            "quality": {"score": 0.8, "label": "Bon", "details": ""},
            "uncertainty": {"score": 0.3, "label": "Faible", "details": ""}
        }),
        "timestamp": datetime.utcnow().isoformat()
    }
