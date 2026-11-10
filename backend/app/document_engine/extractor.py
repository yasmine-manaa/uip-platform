"""
Underwriting Field Extractor with Provenance and Confidence Scoring.
Extracts structured fields from parsed document text using contextual pattern matching,
validation rules, and provenance tags.
"""

from typing import Dict, Any, List, Optional
import re
from datetime import datetime


class FieldExtractor:
    @staticmethod
    def extract_from_text(text: str, doc_id: str, doc_type: str, page: int = 1) -> List[Dict[str, Any]]:
        """
        Extracts underwriting entities with provenance, confidence, and status.
        """
        extracted: List[Dict[str, Any]] = []

        # 1. Driver's License extraction
        if doc_type in ["PERMIS_DE_CONDUIRE", "PROPOSITION_SOUSCRIPTION"]:
            # Date of birth: DD/MM/YYYY or DD-MM-YYYY
            dob_match = re.search(r"(?:né\(e\)\s*le|naissance\s*:?)\s*([0-3]?[0-9][/\-.][0-1]?[0-9][/\-.](?:19|20)\d{2})", text, re.IGNORECASE)
            if dob_match:
                extracted.append({
                    "field_name": "birth_date",
                    "label": "Date de naissance",
                    "value": dob_match.group(1).replace("-", "/"),
                    "confidence": 0.95,
                    "doc_id": doc_id,
                    "page": page,
                    "status": "VALIDATED"
                })

            # License issue date
            lic_match = re.search(r"(?:délivré\s*le|permis\s*le|date\s*délivrance\s*:?)\s*([0-3]?[0-9][/\-.][0-1]?[0-9][/\-.](?:19|20)\d{2})", text, re.IGNORECASE)
            if lic_match:
                extracted.append({
                    "field_name": "licence_date",
                    "label": "Date d'obtention du permis",
                    "value": lic_match.group(1).replace("-", "/"),
                    "confidence": 0.92,
                    "doc_id": doc_id,
                    "page": page,
                    "status": "VALIDATED"
                })

            # License number
            lic_num = re.search(r"(?:permis\s*n°|numéro\s*:?)\s*([0-9]{2}[A-Z0-9]{8,12})", text, re.IGNORECASE)
            if lic_num:
                extracted.append({
                    "field_name": "licence_number",
                    "label": "Numéro de permis",
                    "value": lic_num.group(1),
                    "confidence": 0.90,
                    "doc_id": doc_id,
                    "page": page,
                    "status": "VALIDATED"
                })

        # 2. Relevé d'Information / Claims extraction
        if doc_type in ["RELEVE_INFORMATION", "PROPOSITION_SOUSCRIPTION"]:
            # Bonus-Malus (CRM)
            crm_match = re.search(r"(?:coefficient|crm|bonus-malus|bonus)\s*(?:réduction|majoration)?\s*:?\s*([0-1][\.,][0-9]{2})", text, re.IGNORECASE)
            if crm_match:
                crm_val = float(crm_match.group(1).replace(",", "."))
                extracted.append({
                    "field_name": "bonus_malus",
                    "label": "Coefficient Bonus-Malus (CRM)",
                    "value": crm_val,
                    "confidence": 0.96,
                    "doc_id": doc_id,
                    "page": page,
                    "status": "VALIDATED"
                })

            # Prior claims count
            claims_match = re.search(r"(?:nombre\s*de\s*sinistres?|sinistres?\s*responsables?)\s*:?\s*([0-9]+)", text, re.IGNORECASE)
            if claims_match:
                extracted.append({
                    "field_name": "prior_claims_count",
                    "label": "Nombre de sinistres responsables (3 ans)",
                    "value": int(claims_match.group(1)),
                    "confidence": 0.92,
                    "doc_id": doc_id,
                    "page": page,
                    "status": "VALIDATED"
                })
            elif "aucun sinistre" in text.lower() or "sinistres : néant" in text.lower():
                extracted.append({
                    "field_name": "prior_claims_count",
                    "label": "Nombre de sinistres responsables (3 ans)",
                    "value": 0,
                    "confidence": 0.95,
                    "doc_id": doc_id,
                    "page": page,
                    "status": "VALIDATED"
                })

        # 3. Vehicle Registration / Carte Grise extraction
        if doc_type in ["CARTE_GRISE", "PROPOSITION_SOUSCRIPTION"]:
            # Registration plate: AA-123-AA or 1234 AB 75
            plate_match = re.search(r"\b([A-Z]{2}[-\s]?[0-9]{3}[-\s]?[A-Z]{2})\b", text)
            if plate_match:
                extracted.append({
                    "field_name": "license_plate",
                    "label": "Immatriculation",
                    "value": plate_match.group(1).upper(),
                    "confidence": 0.98,
                    "doc_id": doc_id,
                    "page": page,
                    "status": "VALIDATED"
                })

            # Fiscal power (P.6 on French carte grise or "CV")
            power_match = re.search(r"(?:p\.6|puissance\s*(?:fiscale|administrative)?|chevaux\s*fiscaux)\s*:?\s*([0-9]{1,2})\s*(?:cv)?", text, re.IGNORECASE)
            if power_match:
                extracted.append({
                    "field_name": "vehicle_power",
                    "label": "Puissance fiscale (CV)",
                    "value": int(power_match.group(1)),
                    "confidence": 0.94,
                    "doc_id": doc_id,
                    "page": page,
                    "status": "VALIDATED"
                })

            # Vehicle make and model
            model_match = re.search(r"(?:marque\s*et\s*modèle|d\.1|d\.3)\s*:?\s*([A-Za-z0-9\s\-_]{3,25})", text, re.IGNORECASE)
            if model_match:
                extracted.append({
                    "field_name": "vehicle_model",
                    "label": "Marque / Modèle",
                    "value": model_match.group(1).strip(),
                    "confidence": 0.88,
                    "doc_id": doc_id,
                    "page": page,
                    "status": "VALIDATED"
                })

        # 4. Usage declaration
        usage_match = re.search(r"(?:usage\s*(?:déclaré|véhicule)?\s*:?)\s*(privé|trajet[\-_]travail|professionnel|vtc|taxi)", text, re.IGNORECASE)
        if usage_match:
            u_raw = usage_match.group(1).lower()
            u_norm = "Private" if "privé" in u_raw else ("Commuting" if "travail" in u_raw else ("Taxi_VTC" if "vtc" in u_raw or "taxi" in u_raw else "Professional"))
            extracted.append({
                "field_name": "usage",
                "label": "Usage du véhicule",
                "value": u_norm,
                "confidence": 0.91,
                "doc_id": doc_id,
                "page": page,
                "status": "VALIDATED"
            })

        return extracted
