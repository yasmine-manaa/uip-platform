"""
Deterministic Decision Engine for Underwriting Intelligence Platform.
Section 5.5, 9.2 & 9.3:
Consolidates Risk Level, Data Quality, and Uncertainty into an explainable
provisional recommendation for the human underwriter.
Never makes autonomous refusals.
"""

from typing import Dict, Any, List


class DeterministicDecisionEngine:
    DECISION_CODES = {
        "PROCEED_STANDARD": "Favorable à l'émission - Conditions standards",
        "SPECIAL_TERMS_OFFER": "Proposition avec conditions particulières (Surprime / Franchises)",
        "REQUEST_ADDITIONAL_INFO": "Suspendre - Pièces ou informations complémentaires requises",
        "REQUIRE_SENIOR_REVIEW": "Escalade obligatoire - Examen par souscripteur senior",
        "ANALYSIS_IMPOSSIBLE": "Analyse impossible - Données déficientes ou non conformes"
    }

    @classmethod
    def evaluate(
        cls,
        agent_outputs: Dict[str, Dict[str, Any]],
        case_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Consolidates multi-agent findings into a structured provisional decision.
        Separates Risk Level, Data Quality, and Uncertainty as strictly required by Section 9.2.
        """
        favorable_factors: List[str] = []
        unfavorable_factors: List[str] = []
        reservations: List[str] = []
        required_actions: List[str] = []

        # 1. Inspect Agent 1: Customer Profile
        prof_out = agent_outputs.get("AGENT_01_CUSTOMER_PROFILE", {})
        prof_status = prof_out.get("status")
        prof_alerts = prof_out.get("alerts", [])
        applicant = case_context.get("applicant", {})

        if prof_status == "DATA_DEFICIENT":
            reservations.append("Profil client incomplet.")
            for mf in prof_out.get("missing_fields", []):
                required_actions.append(f"Fournir le champ manquant : '{mf}'.")

        # 2. Inspect Agent 2: Policy & Document
        pol_out = agent_outputs.get("AGENT_02_POLICY_DOCUMENT", {})
        pol_status = pol_out.get("status")
        pol_alerts = pol_out.get("alerts", [])
        for a in pol_alerts:
            msg = a.get("message") if isinstance(a, dict) else a.message
            if "exclusion" in msg.lower() or "sport" in msg.lower() or "vtc" in msg.lower():
                unfavorable_factors.append(f"Alerte contractuelle : {msg}")
                act = a.get("action_required") if isinstance(a, dict) else a.action_required
                if act:
                    required_actions.append(act)

        # 3. Inspect Agent 3: Risk Assessment (Actuarial)
        risk_out = agent_outputs.get("AGENT_03_RISK_ASSESSMENT", {})
        risk_meta = risk_out.get("metadata", {})
        calc = risk_meta.get("actuarial_calculation", {})
        pure_prem = calc.get("pure_premium_eur", 250.0)
        risk_tier = calc.get("risk_tier", "MODERATE")
        uncertainty_level = calc.get("uncertainty_level", "LOW")
        ratio = calc.get("relative_risk_ratio", 1.0)

        if risk_tier == "LOW":
            favorable_factors.append(f"Charge pure technique faible ({pure_prem:.2f} €/an, ratio {ratio:.2f}x).")
        elif risk_tier == "MODERATE":
            favorable_factors.append(f"Charge pure technique conforme au standard ({pure_prem:.2f} €/an).")
        elif risk_tier in ["HIGH", "CRITICAL"]:
            unfavorable_factors.append(f"Charge pure technique élevée ({pure_prem:.2f} €/an, ratio {ratio:.2f}x portefeuille).")

        # 4. Inspect Agent 4: Historical Claims
        clm_out = agent_outputs.get("AGENT_04_HISTORICAL_CLAIMS", {})
        clm_alerts = clm_out.get("alerts", [])
        claims_summary = case_context.get("claims_summary", {})
        bonus_malus = claims_summary.get("bonus_malus")

        if bonus_malus is not None:
            if bonus_malus <= 0.60:
                favorable_factors.append(f"Bonus maximal ou très favorable (CRM {bonus_malus:.2f}).")
            elif bonus_malus >= 1.00:
                unfavorable_factors.append(f"Malus ou absence de réduction (CRM {bonus_malus:.2f}).")
        else:
            reservations.append("Coefficient Bonus-Malus non certifié.")

        # 5. Inspect Agent 6: Governance & Trust
        gov_out = agent_outputs.get("AGENT_06_GOVERNANCE_TRUST", {})
        gov_status = gov_out.get("status")
        gov_meta = gov_out.get("metadata", {})
        contradictions = gov_meta.get("contradictions_detected", [])

        if contradictions:
            for c in contradictions:
                reservations.append(f"Contradiction formelle : {c}")
                required_actions.append("Revue de la contradiction et vérification des pièces justificatives.")

        # --- SEPARATION OF DIMENSIONS ---
        all_missing = []
        for out in agent_outputs.values():
            all_missing.extend(out.get("missing_fields", []))
        all_missing = list(set(all_missing))

        if len(all_missing) >= 3:
            data_quality_rating = "DEFICIENT"
        elif len(all_missing) > 0:
            data_quality_rating = "PARTIAL"
        else:
            data_quality_rating = "COMPLETE"

        risk_level_rating = risk_tier
        uncertainty_rating = uncertainty_level

        if data_quality_rating == "DEFICIENT":
            decision_code = "ANALYSIS_IMPOSSIBLE"
            provisional_recommendation = (
                "Analyse impossible en l'état : Trop d'informations indispensables font défaut. "
                "Le dossier est placé en attente de pièces complémentaires."
            )
        elif len(contradictions) > 0:
            decision_code = "REQUIRE_SENIOR_REVIEW"
            provisional_recommendation = (
                "Escalade souscripteur obligatoire : Des contradictions entre déclarations et pièces ont été relevées. "
                "Examen humain requis avant toute décision."
            )
        elif pol_status == "ESCALATED" or any("exclusion" in u.lower() for u in unfavorable_factors):
            decision_code = "REQUIRE_SENIOR_REVIEW"
            provisional_recommendation = (
                "Escalade souscripteur : Critères d'exclusion ou clauses dérogatoires détectées (véhicule sportif / usage exclu). "
                "Validation hiérarchique requise."
            )
        elif len(all_missing) > 0 or bonus_malus is None:
            decision_code = "REQUEST_ADDITIONAL_INFO"
            provisional_recommendation = (
                "Demande d'informations complémentaires : Des pièces ou déclarations justificatives doivent être produites."
            )
        elif risk_level_rating in ["HIGH", "CRITICAL"]:
            decision_code = "SPECIAL_TERMS_OFFER"
            surprime_pct = min(int((ratio - 1.0) * 100), 80)
            provisional_recommendation = (
                f"Orientation favorable avec aménagement tarifaire : Application recommandée d'une surprime technique de {surprime_pct} % "
                "ou majoration de franchise contractuelle."
            )
            required_actions.append(f"Valider la surprime technique de {surprime_pct} %.")
        else:
            decision_code = "PROCEED_STANDARD"
            provisional_recommendation = (
                "Recommandation favorable : Le dossier satisfait à tous les critères de souscription en conditions standard."
            )

        return {
            "decision_code": decision_code,
            "decision_title": cls.DECISION_CODES.get(decision_code, "Revue Souscripteur"),
            "provisional_recommendation": provisional_recommendation,
            "dimensions": {
                "actuarial_risk_level": risk_level_rating,
                "data_quality": data_quality_rating,
                "model_uncertainty": uncertainty_rating,
            },
            "favorable_factors": favorable_factors,
            "unfavorable_factors": unfavorable_factors,
            "reservations": reservations,
            "required_actions": required_actions,
            "human_review_mandatory": decision_code in ["REQUIRE_SENIOR_REVIEW", "SPECIAL_TERMS_OFFER", "ANALYSIS_IMPOSSIBLE"],
            "disclaimer": (
                "Principe Human-in-the-Loop : Cette recommandation est une aide à la décision. "
                "Elle n'a aucune valeur juridique tant qu'elle n'a pas été formellement validée, "
                "amendée ou refusée par un souscripteur habilité."
            )
        }
