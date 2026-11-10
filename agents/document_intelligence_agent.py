"""
Agent 2 — Document Intelligence Agent
Extrait les informations des documents, vérifie leur cohérence et signale les données manquantes.
Analyse les documents d'assurance (polices, sinistres, pièces d'identité, etc.).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re
import os
from pathlib import Path

# Import RAG system
try:
    from rag.rag_system import rag_system
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


class AgentResult:
    """Contrat commun pour tous les agents"""
    def __init__(self, agent_name: str, status: str, result: Dict[str, Any],
                 confidence: float = 0.0, warnings: List[str] = None,
                 evidence: List[Dict[str, Any]] = None, requires_human_review: bool = False):
        self.agent_name = agent_name
        self.status = status
        self.result = result
        self.confidence = confidence
        self.warnings = warnings or []
        self.evidence = evidence or []
        self.requires_human_review = requires_human_review
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "status": self.status,
            "result": self.result,
            "confidence": self.confidence,
            "warnings": self.warnings,
            "evidence": self.evidence,
            "requires_human_review": self.requires_human_review,
            "timestamp": self.timestamp
        }


class DocumentIntelligenceAgent:
    """
    Agent d'intelligence documentaire.
    Extrait et valide les informations des documents d'assurance.
    """

    def __init__(self):
        self.agent_name = "document_intelligence"
        self.version = "1.0.0"

        # Types de documents supportés
        self.supported_types = [
            "policy", "claim", "id_card", "vehicle_registration",
            "driving_license", "invoice", "other"
        ]

        # Champs requis par type de document
        self.required_fields = {
            "policy": ["policy_number", "insured_name", "vehicle_info", "coverage_period"],
            "claim": ["claim_number", "incident_date", "description", "amount"],
            "id_card": ["full_name", "birth_date", "address"],
            "vehicle_registration": ["registration_number", "brand", "model", "year"],
            "driving_license": ["license_number", "holder_name", "expiry_date", "categories"]
        }

        # Patterns regex pour l'extraction
        self.patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "date": r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b',
            "amount": r'\b\d+([.,]\d{2})?\s*(€|EUR|euros?)\b',
            "policy_number": r'\bPOL[A-Z0-9]{6,}\b',
            "claim_number": r'\bCLM[A-Z0-9]{6,}\b',
            "registration": r'\b[A-Z]{2}\d{3}[A-Z]{2}\b'
        }

    def execute(self, case_context: Dict[str, Any]) -> AgentResult:
        """
        Exécute l'analyse documentaire.

        Args:
            case_context: Contexte du dossier contenant les documents

        Returns:
            AgentResult avec les résultats de l'analyse
        """
        warnings = []
        evidence = []
        extracted_data = {}
        missing_fields = []
        inconsistencies = []

        # Extraire les documents du contexte
        documents = case_context.get("documents", [])

        if not documents:
            warnings.append("Aucun document fourni")
            return AgentResult(
                agent_name=self.agent_name,
                status="NO_DOCUMENTS",
                result={"documents_processed": 0},
                confidence=0.0,
                warnings=warnings,
                evidence=evidence,
                requires_human_review=True
            )

        # Traiter chaque document
        for doc in documents:
            doc_result = self._process_document(doc, case_context)
            extracted_data.update(doc_result.get("extracted_data", {}))
            warnings.extend(doc_result.get("warnings", []))
            missing_fields.extend(doc_result.get("missing_fields", []))
            inconsistencies.extend(doc_result.get("inconsistencies", []))
            evidence.extend(doc_result.get("evidence", []))

        # Utiliser RAG pour améliorer l'extraction si disponible
        if RAG_AVAILABLE and documents:
            rag_enhancement = self._enhance_with_rag(documents, case_context)
            if rag_enhancement.get("success"):
                extracted_data.update(rag_enhancement.get("extracted_data", {}))
                warnings.extend(rag_enhancement.get("warnings", []))
                evidence.extend(rag_enhancement.get("evidence", []))

        # Vérifier la cohérence entre documents et profil
        consistency_check = self._check_consistency(extracted_data, case_context)
        inconsistencies.extend(consistency_check.get("inconsistencies", []))
        warnings.extend(consistency_check.get("warnings", []))

        # Calculer le score de confiance
        confidence = self._calculate_confidence(documents, extracted_data, missing_fields, inconsistencies)

        # Déterminer le statut
        if inconsistencies:
            status = "WARNING"
        elif missing_fields:
            status = "INCOMPLETE"
        else:
            status = "SUCCESS"

        # Résultat
        result = {
            "documents_processed": len(documents),
            "extracted_data": extracted_data,
            "missing_fields": list(set(missing_fields)),
            "inconsistencies": list(set(inconsistencies)),
            "document_types": [doc.get("type", "unknown") for doc in documents]
        }

        return AgentResult(
            agent_name=self.agent_name,
            status=status,
            result=result,
            confidence=confidence,
            warnings=list(set(warnings)),
            evidence=evidence,
            requires_human_review=len(inconsistencies) > 0 or len(missing_fields) > 2
        )

    def _enhance_with_rag(self, documents: List[Dict[str, Any]],
                         case_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Améliore l'extraction en utilisant le système RAG.
        """
        result = {
            "success": False,
            "extracted_data": {},
            "warnings": [],
            "evidence": []
        }

        try:
            # Pour chaque document, utiliser RAG pour extraire des informations
            for doc in documents:
                doc_content = doc.get("content", "")
                doc_type = doc.get("type", "unknown")

                # Rechercher des informations pertinentes dans la base de connaissances
                if doc_type == "policy":
                    # Rechercher des informations sur les polices
                    rag_results = rag_system.knowledge_base.search(
                        f"police assurance {doc_content[:100]}", top_k=3
                    )
                    for rag_result in rag_results:
                        # Extraire des informations supplémentaires
                        if "coverage" in rag_result["text"].lower():
                            result["extracted_data"]["coverage_info"] = rag_result["text"][:200]
                        if "premium" in rag_result["text"].lower():
                            result["extracted_data"]["premium_info"] = rag_result["text"][:200]

                elif doc_type == "claim":
                    # Rechercher des informations sur les sinistres
                    rag_results = rag_system.knowledge_base.search(
                        f"sinistre {doc_content[:100]}", top_k=3
                    )
                    for rag_result in rag_results:
                        if "amount" in rag_result["text"].lower():
                            result["extracted_data"]["claim_amount"] = rag_result["text"][:200]
                        if "damage" in rag_result["text"].lower():
                            result["extracted_data"]["damage_info"] = rag_result["text"][:200]

                # Ajouter des preuves
                result["evidence"].append({
                    "type": "rag_extraction",
                    "document_type": doc_type,
                    "rag_results_count": len(rag_results) if 'rag_results' in locals() else 0
                })

            result["success"] = True

        except Exception as e:
            result["warnings"].append(f"Erreur lors de l'utilisation du RAG: {str(e)}")

        return result

    def _process_document(self, document: Dict[str, Any], case_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite un document individuel.

        Args:
            document: Document à traiter
            case_context: Contexte du dossier

        Returns:
            Dictionnaire avec les résultats du traitement
        """
        warnings = []
        evidence = []
        extracted_data = {}
        missing_fields = []
        inconsistencies = []

        doc_type = document.get("type", "unknown")
        doc_content = document.get("content", "")
        doc_metadata = document.get("metadata", {})

        # Vérifier le type de document
        if doc_type not in self.supported_types:
            warnings.append(f"Type de document non supporté: {doc_type}")

        # Extraire les informations selon le type
        if doc_type == "policy":
            extracted = self._extract_policy_info(doc_content, doc_metadata)
        elif doc_type == "claim":
            extracted = self._extract_claim_info(doc_content, doc_metadata)
        elif doc_type == "id_card":
            extracted = self._extract_id_info(doc_content, doc_metadata)
        elif doc_type == "vehicle_registration":
            extracted = self._extract_vehicle_info(doc_content, doc_metadata)
        elif doc_type == "driving_license":
            extracted = self._extract_license_info(doc_content, doc_metadata)
        else:
            extracted = self._extract_generic_info(doc_content, doc_metadata)

        extracted_data.update(extracted.get("data", {}))
        warnings.extend(extracted.get("warnings", []))
        missing_fields.extend(extracted.get("missing_fields", []))
        inconsistencies.extend(extracted.get("inconsistencies", []))
        evidence.extend(extracted.get("evidence", []))

        return {
            "extracted_data": extracted_data,
            "warnings": warnings,
            "missing_fields": missing_fields,
            "inconsistencies": inconsistencies,
            "evidence": evidence
        }

    def _extract_policy_info(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait les informations d'une police d'assurance"""
        extracted = {}
        warnings = []
        missing_fields = []
        inconsistencies = []
        evidence = []

        # Extraire le numéro de police
        policy_match = re.search(self.patterns["policy_number"], content, re.IGNORECASE)
        if policy_match:
            extracted["policy_number"] = policy_match.group()
            evidence.append({"field": "policy_number", "value": policy_match.group(), "source": "regex"})
        else:
            missing_fields.append("policy_number")

        # Extraire les dates de couverture
        date_matches = re.findall(self.patterns["date"], content)
        if len(date_matches) >= 2:
            extracted["coverage_start"] = date_matches[0]
            extracted["coverage_end"] = date_matches[1]
            evidence.append({"field": "coverage_period", "value": f"{date_matches[0]} - {date_matches[1]}", "source": "regex"})
        else:
            missing_fields.append("coverage_period")

        # Extraire le nom de l'assuré
        name_match = re.search(r'Nom:\s*([A-Za-z\s]+)', content, re.IGNORECASE)
        if name_match:
            extracted["insured_name"] = name_match.group(1).strip()
            evidence.append({"field": "insured_name", "value": extracted["insured_name"], "source": "regex"})
        else:
            missing_fields.append("insured_name")

        return {
            "data": extracted,
            "warnings": warnings,
            "missing_fields": missing_fields,
            "inconsistencies": inconsistencies,
            "evidence": evidence
        }

    def _extract_claim_info(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait les informations d'un sinistre"""
        extracted = {}
        warnings = []
        missing_fields = []
        inconsistencies = []
        evidence = []

        # Extraire le numéro de sinistre
        claim_match = re.search(self.patterns["claim_number"], content, re.IGNORECASE)
        if claim_match:
            extracted["claim_number"] = claim_match.group()
            evidence.append({"field": "claim_number", "value": claim_match.group(), "source": "regex"})
        else:
            missing_fields.append("claim_number")

        # Extraire la date de l'incident
        date_match = re.search(self.patterns["date"], content)
        if date_match:
            extracted["incident_date"] = date_match.group()
            evidence.append({"field": "incident_date", "value": date_match.group(), "source": "regex"})
        else:
            missing_fields.append("incident_date")

        # Extraire le montant
        amount_match = re.search(self.patterns["amount"], content, re.IGNORECASE)
        if amount_match:
            amount_str = amount_match.group()
            # Nettoyer et convertir le montant
            amount_clean = re.sub(r'[^\d.,]', '', amount_str)
            amount_clean = amount_clean.replace(',', '.')
            try:
                extracted["amount"] = float(amount_clean)
                evidence.append({"field": "amount", "value": extracted["amount"], "source": "regex"})
            except ValueError:
                warnings.append(f"Impossible de parser le montant: {amount_str}")
                missing_fields.append("amount")
        else:
            missing_fields.append("amount")

        return {
            "data": extracted,
            "warnings": warnings,
            "missing_fields": missing_fields,
            "inconsistencies": inconsistencies,
            "evidence": evidence
        }

    def _extract_id_info(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait les informations d'une pièce d'identité"""
        extracted = {}
        warnings = []
        missing_fields = []
        inconsistencies = []
        evidence = []

        # Extraire le nom complet
        name_match = re.search(r'Nom:\s*([A-Za-z\s]+)', content, re.IGNORECASE)
        if name_match:
            extracted["full_name"] = name_match.group(1).strip()
            evidence.append({"field": "full_name", "value": extracted["full_name"], "source": "regex"})
        else:
            missing_fields.append("full_name")

        # Extraire la date de naissance
        birth_match = re.search(r'Naissance:\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})', content, re.IGNORECASE)
        if birth_match:
            extracted["birth_date"] = birth_match.group(1)
            evidence.append({"field": "birth_date", "value": extracted["birth_date"], "source": "regex"})
        else:
            missing_fields.append("birth_date")

        return {
            "data": extracted,
            "warnings": warnings,
            "missing_fields": missing_fields,
            "inconsistencies": inconsistencies,
            "evidence": evidence
        }

    def _extract_vehicle_info(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait les informations d'un véhicule"""
        extracted = {}
        warnings = []
        missing_fields = []
        inconsistencies = []
        evidence = []

        # Extraire le numéro d'immatriculation
        reg_match = re.search(self.patterns["registration"], content, re.IGNORECASE)
        if reg_match:
            extracted["registration_number"] = reg_match.group()
            evidence.append({"field": "registration_number", "value": reg_match.group(), "source": "regex"})
        else:
            missing_fields.append("registration_number")

        # Extraire la marque
        brand_match = re.search(r'Marque:\s*([A-Za-z]+)', content, re.IGNORECASE)
        if brand_match:
            extracted["brand"] = brand_match.group(1)
            evidence.append({"field": "brand", "value": extracted["brand"], "source": "regex"})
        else:
            missing_fields.append("brand")

        return {
            "data": extracted,
            "warnings": warnings,
            "missing_fields": missing_fields,
            "inconsistencies": inconsistencies,
            "evidence": evidence
        }

    def _extract_license_info(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait les informations d'un permis de conduire"""
        extracted = {}
        warnings = []
        missing_fields = []
        inconsistencies = []
        evidence = []

        # Extraire le numéro de permis
        license_match = re.search(r'Permis:\s*([A-Z0-9]+)', content, re.IGNORECASE)
        if license_match:
            extracted["license_number"] = license_match.group(1)
            evidence.append({"field": "license_number", "value": extracted["license_number"], "source": "regex"})
        else:
            missing_fields.append("license_number")

        # Extraire la date d'expiration
        expiry_match = re.search(r'Expiration:\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})', content, re.IGNORECASE)
        if expiry_match:
            extracted["expiry_date"] = expiry_match.group(1)
            evidence.append({"field": "expiry_date", "value": extracted["expiry_date"], "source": "regex"})
        else:
            missing_fields.append("expiry_date")

        return {
            "data": extracted,
            "warnings": warnings,
            "missing_fields": missing_fields,
            "inconsistencies": inconsistencies,
            "evidence": evidence
        }

    def _extract_generic_info(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait les informations génériques d'un document"""
        extracted = {}
        warnings = []
        missing_fields = []
        inconsistencies = []
        evidence = []

        # Extraire les emails
        emails = re.findall(self.patterns["email"], content)
        if emails:
            extracted["emails"] = emails
            evidence.append({"field": "emails", "value": emails, "source": "regex"})

        # Extraire les téléphones
        phones = re.findall(self.patterns["phone"], content)
        if phones:
            extracted["phones"] = phones
            evidence.append({"field": "phones", "value": phones, "source": "regex"})

        return {
            "data": extracted,
            "warnings": warnings,
            "missing_fields": missing_fields,
            "inconsistencies": inconsistencies,
            "evidence": evidence
        }

    def _check_consistency(self, extracted_data: Dict[str, Any], case_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Vérifie la cohérence entre les données extraites et le profil client.

        Args:
            extracted_data: Données extraites des documents
            case_context: Contexte du dossier

        Returns:
            Dictionnaire avec les incohérences trouvées
        """
        inconsistencies = []
        warnings = []

        # Vérifier la cohérence du nom
        applicant_name = case_context.get("applicant", {}).get("full_name", "")
        if "insured_name" in extracted_data and applicant_name:
            if extracted_data["insured_name"].lower() != applicant_name.lower():
                inconsistencies.append(f"Nom assuré ({extracted_data['insured_name']}) différent du profil ({applicant_name})")
                warnings.append("Incohérence de nom entre documents et profil")

        # Vérifier la cohérence de la date de naissance
        if "birth_date" in extracted_data and "driver_age" in case_context.get("applicant", {}):
            # Calculer l'âge à partir de la date de naissance
            try:
                birth_date = extracted_data["birth_date"]
                # Parser la date (format DD/MM/YYYY ou DD-MM-YYYY)
                parts = re.split(r'[/\-]', birth_date)
                if len(parts) == 3:
                    day, month, year = map(int, parts)
                    birth_year = year if year > 100 else 2000 + year
                    calculated_age = datetime.now().year - birth_year
                    declared_age = case_context["applicant"]["driver_age"]

                    if abs(calculated_age - declared_age) > 1:
                        inconsistencies.append(f"Âge calculé ({calculated_age}) différent de l'âge déclaré ({declared_age})")
                        warnings.append("Incohérence d'âge entre documents et profil")
            except Exception as e:
                warnings.append(f"Erreur lors du calcul de l'âge: {e}")

        return {
            "inconsistencies": inconsistencies,
            "warnings": warnings
        }

    def _calculate_confidence(self, documents: List[Dict[str, Any]], extracted_data: Dict[str, Any],
                             missing_fields: List[str], inconsistencies: List[str]) -> float:
        """
        Calcule le score de confiance basé sur la qualité des documents.
        """
        # Score de base
        base_score = 1.0

        # Pénalité pour les documents manquants
        doc_penalty = 0.0
        if not documents:
            doc_penalty = 1.0

        # Pénalité pour les champs manquants
        missing_penalty = len(missing_fields) * 0.05

        # Pénalité pour les incohérences
        inconsistency_penalty = len(inconsistencies) * 0.2

        # Bonus pour les documents bien structurés
        structure_bonus = 0.0
        for doc in documents:
            if doc.get("type") in self.supported_types:
                structure_bonus += 0.05

        confidence = max(0.0, base_score - doc_penalty - missing_penalty - inconsistency_penalty + structure_bonus)
        return round(min(1.0, confidence), 2)


# Instance globale de l'agent
document_intelligence_agent = DocumentIntelligenceAgent()
