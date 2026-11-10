"""
Demo Data Seeder for Underwriting Intelligence Platform.
Populates realistic demonstration cases, documents, and pre-computed analyses
for immediate demonstration of all 6 platform views.
"""

import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.case import Case, Document, AgentRun, HumanReview, AuditEvent
from app.orchestrator.graph import execute_underwriting_workflow
from app.document_engine.classifier import DocumentClassifier
from app.document_engine.extractor import FieldExtractor


DEMO_CASES = [
    {
        "id": "CAS-2026-001",
        "applicant_name": "Claire Lefebvre",
        "coverage_requested": "Tous Risques",
        "input": {
            "case_id": "CAS-2026-001",
            "applicant": {
                "full_name": "Claire Lefebvre",
                "driver_age": 38,
                "licence_years": 18,
                "usage": "Commuting",
                "postal_code": "44000",
                "annual_mileage": 13000
            },
            "vehicle": {
                "vehicle_model": "RENAULT CLIO",
                "vehicle_power": 5,
                "vehicle_age": 4,
                "vehicle_genre": "VP",
                "license_plate": "EK-892-FZ"
            },
            "claims_summary": {
                "bonus_malus": 0.50,
                "prior_claims_count": 0,
                "cancelled_by_previous_insurer": False
            },
            "coverage_requested": "Tous Risques",
            "area_density": 4
        },
        "sample_doc_text": (
            "RÉPUBLIQUE FRANÇAISE - PERMIS DE CONDUIRE\n"
            "Titulaire : Claire Lefebvre\n"
            "Né(e) le : 14/05/1988\n"
            "Date de délivrance : 22/06/2008\n"
            "Numéro : 08AB12345678\n"
            "Catégorie B - Véhicules légers"
        ),
        "doc_name": "Permis_Claire_Lefebvre.txt"
    },
    {
        "id": "CAS-2026-002",
        "applicant_name": "Lucas Martin",
        "coverage_requested": "Tous Risques",
        "input": {
            "case_id": "CAS-2026-002",
            "applicant": {
                "full_name": "Lucas Martin",
                "driver_age": 20,
                "licence_years": 1,
                "usage": "Private",
                "postal_code": "75008",
                "annual_mileage": 16000
            },
            "vehicle": {
                "vehicle_model": "BMW SERIE 3",
                "vehicle_power": 12,
                "vehicle_age": 2,
                "vehicle_genre": "VP",
                "license_plate": "GH-456-JK"
            },
            "claims_summary": {
                "bonus_malus": 1.00,
                "prior_claims_count": 0,
                "cancelled_by_previous_insurer": False
            },
            "coverage_requested": "Tous Risques",
            "area_density": 6
        },
        "sample_doc_text": (
            "CERTIFICAT D'IMMATRICULATION\n"
            "Numéro d'immatriculation : GH-456-JK\n"
            "Marque et Modèle : BMW SERIE 3\n"
            "Puissance fiscale (P.6) : 12 CV\n"
            "Genre national : VP"
        ),
        "doc_name": "CarteGrise_Lucas_Martin.txt"
    },
    {
        "id": "CAS-2026-003",
        "applicant_name": "Karim Benali",
        "coverage_requested": "Tous Risques",
        "input": {
            "case_id": "CAS-2026-003",
            "applicant": {
                "full_name": "Karim Benali",
                "driver_age": 36,
                "licence_years": 14,
                "usage": "Private",  # Declared private, but vehicle is TAXI -> CONTRADICTION!
                "postal_code": "93200",
                "annual_mileage": 35000
            },
            "vehicle": {
                "vehicle_model": "PEUGEOT 508",
                "vehicle_power": 8,
                "vehicle_age": 2,
                "vehicle_genre": "TAXI",
                "license_plate": "LM-789-PQ"
            },
            "claims_summary": {
                "bonus_malus": 0.72,
                "prior_claims_count": 0,
                "cancelled_by_previous_insurer": False
            },
            "coverage_requested": "Tous Risques",
            "area_density": 5
        },
        "sample_doc_text": (
            "CERTIFICAT D'IMMATRICULATION - VÉHICULE PROFESSIONNEL\n"
            "Numéro d'immatriculation : LM-789-PQ\n"
            "Marque et Modèle : PEUGEOT 508\n"
            "Puissance administrative (P.6) : 8 CV\n"
            "Genre national (J.1) : TAXI / Transport rémunéré de personnes"
        ),
        "doc_name": "CarteGrise_Karim_Benali.txt"
    },
    {
        "id": "CAS-2026-004",
        "applicant_name": "Sophie Girard",
        "coverage_requested": "Tiers Étendu",
        "input": {
            "case_id": "CAS-2026-004",
            "applicant": {
                "full_name": "Sophie Girard",
                "driver_age": 27,
                "licence_years": 6,
                "usage": "Commuting",
                "postal_code": "69003",
                "annual_mileage": 11000
            },
            "vehicle": {
                "vehicle_model": "VOLKSWAGEN POLO",
                "vehicle_power": 5,
                "vehicle_age": 6,
                "vehicle_genre": "VP",
                "license_plate": "RS-234-TU"
            },
            "claims_summary": {
                "bonus_malus": None,  # Missing CRM proof -> REQUEST_ADDITIONAL_INFO
                "prior_claims_count": 0,
                "cancelled_by_previous_insurer": False
            },
            "coverage_requested": "Tiers Étendu",
            "area_density": 5
        },
        "sample_doc_text": (
            "PROPOSITION D'ASSURANCE AUTOMOBILE\n"
            "Demandeur : Sophie Girard\n"
            "Usage déclaré : Trajet-travail\n"
            "Garanties souhaitées : Tiers Étendu\n"
            "Attestation Bonus-Malus : En attente de transmission par l'ancien assureur"
        ),
        "doc_name": "Proposition_Sophie_Girard.txt"
    }
]


def seed_demo_cases(db: Session):
    """
    Populates demo cases, processes analysis, and creates initial audit chain.
    """
    for item in DEMO_CASES:
        existing = db.query(Case).filter(Case.id == item["id"]).first()
        if existing:
            continue

        raw_input = item["input"]
        case = Case(
            id=item["id"],
            applicant_name=item["applicant_name"],
            status="DRAFT",
            coverage_requested=item["coverage_requested"],
            raw_input_json=json.dumps(raw_input)
        )
        db.add(case)
        db.flush()

        # Audit event 1
        audit1 = AuditEvent.create_event(
            case_id=item["id"],
            event_type="CASE_CREATED",
            actor="Système d'ingestion Démo",
            details={"applicant": item["applicant_name"]}
        )
        db.add(audit1)
        db.flush()

        # Document
        classification = DocumentClassifier.classify(item["sample_doc_text"], item["doc_name"])
        doc_id = f"DOC-{item['id']}"
        extracted = FieldExtractor.extract_from_text(item["sample_doc_text"], doc_id, classification["document_type"])
        doc = Document(
            id=doc_id,
            case_id=item["id"],
            filename=item["doc_name"],
            doc_type=classification["document_type"],
            doc_label=classification["document_label"],
            page_count=1,
            ocr_status="SUCCESS",
            confidence=classification["confidence"],
            raw_text=item["sample_doc_text"],
            extracted_fields_json=json.dumps(extracted)
        )
        db.add(doc)
        db.flush()

        # Audit event 2
        audit2 = AuditEvent.create_event(
            case_id=item["id"],
            event_type="DOCUMENT_UPLOADED",
            actor="Système Démo",
            details={"doc_name": item["doc_name"], "doc_type": classification["document_type"]},
            prev_hash=audit1.current_hash
        )
        db.add(audit2)
        db.flush()

        # Run multi-agent analysis
        result = execute_underwriting_workflow(raw_input)
        agent_outputs = result.get("agent_outputs", {})

        for a_id, out in agent_outputs.items():
            run_rec = AgentRun(
                id=f"RUN-{item['id']}-{a_id}",
                case_id=item["id"],
                agent_id=a_id,
                agent_name=out.get("agent_name", a_id),
                version=out.get("version", "1.0.0"),
                status=out.get("status", "SUCCESS"),
                confidence_score=out.get("confidence_score", 1.0),
                findings_json=json.dumps(out.get("findings", [])),
                alerts_json=json.dumps(out.get("alerts", [])),
                evidence_json=json.dumps(out.get("evidence", [])),
                sources_json=json.dumps(out.get("sources", [])),
                missing_fields_json=json.dumps(out.get("missing_fields", []))
            )
            db.add(run_rec)
        db.flush()

        prov_dec = result.get("provisional_decision", {})
        risk_out = agent_outputs.get("AGENT_03_RISK_ASSESSMENT", {})
        act_calc = risk_out.get("metadata", {}).get("actuarial_calculation", {})

        case.status = "UNDER_REVIEW"
        case.decision_code = prov_dec.get("decision_code")
        case.provisional_recommendation = prov_dec.get("provisional_recommendation")
        case.risk_tier = act_calc.get("risk_tier", "MODERATE")
        case.pure_premium_eur = act_calc.get("pure_premium_eur")

        # Audit event 3
        audit3 = AuditEvent.create_event(
            case_id=item["id"],
            event_type="ANALYSIS_EXECUTED",
            actor="LangGraph Orchestrator",
            details={"decision_code": case.decision_code, "risk_tier": case.risk_tier},
            prev_hash=audit2.current_hash
        )
        db.add(audit3)
        db.commit()
