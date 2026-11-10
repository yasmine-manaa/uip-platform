"""
Document Classification Module.
Identifies insurance document types from textual cues, keywords, and structural markers.
"""

from typing import Dict, Any, Tuple
import re


class DocumentClassifier:
    RULES = {
        "PERMIS_DE_CONDUIRE": {
            "title": "Permis de Conduire",
            "keywords": ["permis de conduire", "catégorie b", "prefecture", "titulaire", "date de délivrance", "ministère de l'intérieur"],
            "weight": 2.0
        },
        "RELEVE_INFORMATION": {
            "title": "Relevé d'Information Sinistres",
            "keywords": ["relevé d'information", "coefficient de réduction-majoration", "bonus-malus", "crm", "sinistre responsable", "antécédents", "art. a. 121-1"],
            "weight": 2.5
        },
        "CARTE_GRISE": {
            "title": "Certificat d'Immatriculation (Carte Grise)",
            "keywords": ["certificat d'immatriculation", "immatriculation", "puissance nette", "chevaux fiscaux", "numéro d'identification", "châssis", "genre national", "vp"],
            "weight": 2.2
        },
        "JUSTIFICATIF_DOMICILE": {
            "title": "Justificatif de Domicile",
            "keywords": ["facture d'électricité", "quittance de loyer", "avis d'imposition", "titulaire du contrat", "lieu de consommation", "adresse de facturation"],
            "weight": 1.8
        },
        "PROPOSITION_SOUSCRIPTION": {
            "title": "Formulaire de Proposition de Souscription",
            "keywords": ["formulaire de souscription", "proposition d'assurance", "usage déclaré", "garanties souhaitées", "conducteur désigné", "déclaration du risque"],
            "weight": 2.0
        },
        "ATTTESTATION_ASSURANCE": {
            "title": "Attestation d'Assurance",
            "keywords": ["attestation d'assurance", "numéro de police", "assuré", "véhicule", "immatriculation", "début de couverture", "fin de couverture", "garantie", "assurance automobile"],
            "weight": 3.0
        }
    }

    @classmethod
    def classify(cls, text: str, filename: str = "") -> Dict[str, Any]:
        """
        Classifies document text and calculates confidence score.
        """
        clean_text = (text + " " + filename).lower()
        best_type = "DOCUMENT_NON_RECONNU"
        best_score = 0.0
        matched_keywords = []

        for doc_type, rule in cls.RULES.items():
            matches = [kw for kw in rule["keywords"] if kw in clean_text]
            score = len(matches) * rule["weight"]
            if score > best_score and len(matches) >= 1:
                best_score = score
                best_type = doc_type
                matched_keywords = matches

        confidence = min(round(best_score / 6.0, 2), 0.98) if best_score > 0 else 0.10

        return {
            "document_type": best_type,
            "document_label": cls.RULES.get(best_type, {}).get("title", "Document Inconnu"),
            "confidence": confidence,
            "matched_indicators": matched_keywords,
            "requires_human_verification": confidence < 0.60
        }
