"""
Comprehensive Test Suite for Underwriting Intelligence Platform (UIP).
Validates:
1. Pure Actuarial Engine (GLM Poisson, GLM Gamma, XGBoost, SHAP, CI)
2. Document Intelligence (PyMuPDF, Classifier, Extractor, Citations RAG)
3. 6 Specialized Agents output contracts
4. Multi-Agent Orchestration & Decision Engine Matrix
5. Scientific Validation Benchmark (Configs A, B, C, D)
6. Cryptographic Audit Chaining Integrity
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["LOKY_MAX_CPU_COUNT"] = "1"
import sys
import unittest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_dir)

from app.actuarial.trainer import actuarial_engine
from app.document_engine.classifier import DocumentClassifier
from app.document_engine.extractor import FieldExtractor
from app.document_engine.vector_store import policy_vector_store
from app.agents.profile_agent import CustomerProfileAgent
from app.agents.policy_agent import PolicyDocumentAgent
from app.agents.risk_agent import RiskAssessmentAgent
from app.agents.claims_agent import HistoricalClaimsAgent
from app.agents.external_agent import ExternalIntelligenceAgent
from app.agents.governance_agent import GovernanceTrustAgent
from app.orchestrator.graph import execute_underwriting_workflow
from app.evaluation.benchmark_runner import ScientificBenchmarkRunner
from app.models.case import AuditEvent


class TestUnderwritingPlatform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        actuarial_engine.train_and_calibrate(n_samples=500)

    def test_01_actuarial_engine_predictions(self):
        res = actuarial_engine.evaluate_risk({
            "driver_age": 30,
            "licence_years": 10,
            "bonus_malus": 0.85,
            "vehicle_power": 6,
            "prior_claims_count": 0
        })
        calc = res["calculation"]
        self.assertIn("pure_premium_eur", calc)
        self.assertGreater(calc["pure_premium_eur"], 0.0)
        self.assertIn(calc["risk_tier"], ["LOW", "MODERATE", "HIGH", "CRITICAL"])
        self.assertIn("AVERTISSEMENT ACTUARIEL", calc["disclaimer"])
        self.assertIn("shap_factors", res["explainability"])

    def test_02_document_classification_and_extraction(self):
        permis_text = "RÉPUBLIQUE FRANÇAISE - PERMIS DE CONDUIRE Titulaire : Jean Dupont Né(e) le 12/03/1990 délivré le 15/04/2010"
        classification = DocumentClassifier.classify(permis_text)
        self.assertEqual(classification["document_type"], "PERMIS_DE_CONDUIRE")
        self.assertGreater(classification["confidence"], 0.60)

        extracted = FieldExtractor.extract_from_text(permis_text, "DOC-1", "PERMIS_DE_CONDUIRE")
        field_names = [f["field_name"] for f in extracted]
        self.assertIn("birth_date", field_names)
        self.assertIn("licence_date", field_names)

    def test_03_policy_rag_citations(self):
        results = policy_vector_store.search("Garantie Responsabilité Civile dommages corporels", top_k=2)
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertIn("citation_id", top)
        self.assertIn("doc_title", top)
        self.assertIn("page", top)
        self.assertIn("article", top)

    def test_04_customer_profile_agent_validation(self):
        agent = CustomerProfileAgent()
        # Test minor rejection
        out_minor = agent.execute({"applicant": {"driver_age": 16, "licence_years": 0, "usage": "Private", "postal_code": "75001"}})
        self.assertEqual(out_minor.status, "ESCALATED")
        self.assertTrue(any(a.code == "PROF_AGE_UNDERAGE" for a in out_minor.alerts))

    def test_05_policy_agent_sport_novice_exclusion(self):
        agent = PolicyDocumentAgent()
        out = agent.execute({
            "applicant": {"licence_years": 1, "usage": "Private"},
            "vehicle": {"vehicle_power": 14},
            "coverage_requested": "Tous Risques"
        })
        self.assertEqual(out.status, "ESCALATED")
        self.assertTrue(any(a.code == "POL_SPORT_NOVICE_EXCLUSION" for a in out.alerts))

    def test_06_claims_agent_contradiction(self):
        agent = HistoricalClaimsAgent()
        # CRM 0.50 with 2 at-fault claims is a contradiction
        out = agent.execute({
            "claims_summary": {"bonus_malus": 0.50, "prior_claims_count": 2}
        })
        self.assertEqual(out.status, "ESCALATED")
        self.assertTrue(any(a.code == "CLM_CRM_CONTRADICTION" for a in out.alerts))

    def test_07_full_multi_agent_workflow(self):
        res = execute_underwriting_workflow({
            "case_id": "TEST-FULL",
            "applicant": {"full_name": "Paul Durand", "driver_age": 45, "licence_years": 25, "usage": "Commuting", "postal_code": "44000"},
            "vehicle": {"vehicle_model": "RENAULT CLIO", "vehicle_power": 5, "vehicle_age": 4, "vehicle_genre": "VP"},
            "claims_summary": {"bonus_malus": 0.50, "prior_claims_count": 0},
            "coverage_requested": "Tous Risques",
            "area_density": 3
        })
        self.assertEqual(res["status"], "COMPLETED")
        self.assertEqual(len(res["agent_outputs"]), 6)
        dec = res["provisional_decision"]
        self.assertEqual(dec["decision_code"], "PROCEED_STANDARD")
        self.assertFalse(dec["human_review_mandatory"])

    def test_08_scientific_benchmark(self):
        bench = ScientificBenchmarkRunner.run_benchmark()
        self.assertIn("config_A_actuarial_baseline", bench)
        self.assertIn("config_D_orchestrated_uip", bench)
        comp = bench["metrics_comparison"]
        self.assertEqual(len(comp["configurations"]), 4)
        config_d = next(c for c in comp["configurations"] if c["id"] == "Config D")
        self.assertEqual(config_d["contradiction_detection_rate"], 100.0)
        self.assertGreater(config_d["auditability_score"], 95.0)

    def test_09_cryptographic_audit_trail(self):
        ev1 = AuditEvent.create_event("CAS-AUDIT", "EVENT_1", "Actor 1", {"step": 1}, prev_hash="")
        ev2 = AuditEvent.create_event("CAS-AUDIT", "EVENT_2", "Actor 2", {"step": 2}, prev_hash=ev1.current_hash)
        self.assertEqual(ev2.previous_hash, ev1.current_hash)
        self.assertNotEqual(ev1.current_hash, ev2.current_hash)


if __name__ == "__main__":
    unittest.main()
