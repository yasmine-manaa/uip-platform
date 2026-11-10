"""
Reference Policy Corpus for Underwriting Intelligence Platform (UIP).
Represents official contractual terms, general conditions, endorsements,
guarantees, deductibles, and strict exclusions for French Auto Insurance.
Each section is tagged with verifiable citations: document, page, article, and exact text.
"""

from typing import List, Dict, Any

POLICY_CORPUS: List[Dict[str, Any]] = [
    {
        "doc_id": "CG-AUTO-2026",
        "doc_title": "Conditions Générales Automobile - Réf. POL-AUTO-2026-V1",
        "page": 4,
        "article": "Art. 2.1 - Responsabilité Civile Légale",
        "category": "Garantie Obligatoire",
        "content": (
            "Conformément à l'article L. 211-1 du Code des assurances, la garantie Responsabilité Civile "
            "couvre les conséquences pécuniaires des dommages corporels et matériels causés aux tiers "
            "par le véhicule désigné aux Conditions Particulières. Les dommages corporels subis par les tiers "
            "sont couverts sans limitation de somme. Les dommages aux biens sont plafonnés à 100 000 000 €."
        ),
        "tags": ["responsabilite_civile", "tiers", "obligatoire", "plafond"]
    },
    {
        "doc_id": "CG-AUTO-2026",
        "doc_title": "Conditions Générales Automobile - Réf. POL-AUTO-2026-V1",
        "page": 7,
        "article": "Art. 3.2 - Garantie Dommages Tous Accidents (Tous Risques)",
        "category": "Garantie Optionnelle",
        "content": (
            "Sont indemnisés les dégâts matériels subis par le véhicule assuré consécutifs à une collision avec un "
            "autre véhicule, un piéton ou un animal, ainsi qu'au versement sans collision préalable, ou à des actes de "
            "vandalisme expressément constatés par dépôt de plainte. Franchise contractuelle standard : 450 € par sinistre "
            "ou 10 % du montant des réparations avec un minimum de 300 €."
        ),
        "tags": ["tous_risques", "dommages", "collision", "franchise"]
    },
    {
        "doc_id": "CG-AUTO-2026",
        "doc_title": "Conditions Générales Automobile - Réf. POL-AUTO-2026-V1",
        "page": 11,
        "article": "Art. 4.1 - Exclusions Légales Générales",
        "category": "Exclusion",
        "content": (
            "Sont formellement et irrévocablement exclus de toute couverture : "
            "1. Les dommages survenus lorsque le conducteur ne possède pas de permis de conduire valide ou en état de suspension/annulation. "
            "2. Les sinistres occasionnés intentionnellement ou avec dol par le souscripteur ou le conducteur autorisé (Art. L. 113-1). "
            "3. L'utilisation du véhicule pour le transport onéreux de personnes (activité taxi, VTC, covoiturage commercial) "
            "sans souscription préalable et formelle de l'avenant d'usage professionnel spécifique."
        ),
        "tags": ["exclusion", "permis", "vtc_taxi", "transport_onereux", "dol"]
    },
    {
        "doc_id": "CG-AUTO-2026",
        "doc_title": "Conditions Générales Automobile - Réf. POL-AUTO-2026-V1",
        "page": 12,
        "article": "Art. 4.3 - Sanction des Fausses Déclarations à la Souscription",
        "category": "Règle de Souscription",
        "content": (
            "Toute réticence ou fausse déclaration intentionnelle de la part du souscripteur modifiant l'opinion du risque "
            "entraîne la nullité du contrat au titre de l'article L. 113-8 du Code des assurances. En cas de fausse déclaration "
            "non intentionnelle constatée avant sinistre, l'assureur applique soit un ajustement de prime soit la résiliation sous dix jours "
            "(Art. L. 113-9)."
        ),
        "tags": ["fraude", "nullite", "declaration", "l113-8", "l113-9"]
    },
    {
        "doc_id": "CS-PNO-2026",
        "doc_title": "Convention Spéciale Véhicules Puissants & Conducteurs Novices - Réf. CS-PNO-2026",
        "page": 2,
        "article": "Art. 1.2 - Critères d'Acceptation Véhicules Sportifs / Puissance Élevée",
        "category": "Règle de Souscription",
        "content": (
            "Tout véhicule dont la puissance fiscale est égale ou supérieure à 10 Chevaux Fiscaux (CV) ou dont le rapport "
            "poids/puissance excède 110 kW/tonne fait l'objet d'un examen obligatoire par le comité de souscription. "
            "Conditions requises : le conducteur principal doit justifier d'au moins 3 années ininterrompues de permis "
            "et d'un coefficient de réduction-majoration (bonus) inférieur ou égal à 0.85 sans sinistre responsable au cours des 24 derniers mois."
        ),
        "tags": ["puissance", "sportif", "conducteur_novice", "seuil_puissance", "escalade"]
    },
    {
        "doc_id": "CS-PNO-2026",
        "doc_title": "Convention Spéciale Véhicules Puissants & Conducteurs Novices - Réf. CS-PNO-2026",
        "page": 3,
        "article": "Art. 2.1 - Clause Jeune Conducteur et Franchise Novice",
        "category": "Franchise Spécifique",
        "content": (
            "Pour tout conducteur titulaire du permis depuis moins de 36 mois, une franchise novice supplémentaire de 750 € "
            "s'ajoute à la franchise contractuelle de base pour tout sinistre matériel responsable. L'accès à la formule Tous Risques "
            "sur les véhicules d'une puissance supérieure à 8 CV requiert l'accord formel d'un souscripteur senior."
        ),
        "tags": ["jeune_conducteur", "novice", "franchise_majoree", "autorisation_senior"]
    },
    {
        "doc_id": "GUIDE-TARIF-2026",
        "doc_title": "Guide Technique de Tarification et Souscription - Direction Technique",
        "page": 15,
        "article": "Section 5 - Règles de Gestion des Antécédents de Sinistralité",
        "category": "Directives Souscription",
        "content": (
            "Règle R-SIN-01 : Tout dossier présentant plus de 2 sinistres matériels responsables au cours des 36 derniers mois "
            "doit être orienté en revue humaine obligatoire avec calcul d'une surprime technique minimale de 30 %. "
            "Règle R-SIN-02 : En présence d'un antécédent de résiliation pour non-paiement ou pour sinistre par l'assureur précédent, "
            "le dossier requiert impérativement la fourniture du relevé d'information intégral sur 5 ans."
        ),
        "tags": ["antecedents", "sinistres", "surprime", "resiliation_anterieure"]
    }
]
