# Underwriting Intelligence Platform (UIP)

> Plateforme d'aide à la souscription automobile multi-agents, conforme RGPD et droit français des assurances.

**Emplacement de la base de données**: `backend/uip_platform.db` (SQLite pour développement)

**Document de conformité**: Voir [CONFORMITE_CDC.md](./CONFORMITE_CDC.md) pour l'analyse détaillée de la conformité au cahier des charges.

**Plan de développement**:
1. ✅ Télécharger freMTPL2freq et freMTPL2sev
2. ✅ Faire une analyse exploratoire des données (EDA)
3. ✅ Construire le modèle de prédiction de fréquence (GLM Poisson)
4. ✅ Construire le modèle de prédiction de sévérité (GLM Gamma)
5. ✅ Construire le moteur actuariel
6. ✅ Développer les agents indépendamment
7. ✅ Construire l'orchestration LangGraph
8. ✅ Intégrer le RAG et les documents
9. ⏭️ Développer le frontend
10. ⏭️ Effectuer les expérimentations comparatives

---

## Architecture

```
uip-platform/
├── datasets/          # Données freMTPL2
│   ├── raw/           # freMTPL2freq.csv, freMTPL2sev.csv
│   └── processed/     # Données traitées pour modélisation
├── notebooks/         # Analyse exploratoire des données
│   └── EDA.ipynb      # Exploratory Data Analysis
├── models/            # Modèles actuariels
│   ├── frequency_model/  # GLM Poisson pour la fréquence
│   ├── severity_model/   # GLM Gamma pour la sévérité
│   └── actuarial_engine/ # Moteur actuariel (prédictions + incertitude)
├── agents/            # Agents spécialisés (indépendants)
│   ├── customer_profile_agent.py      # Agent 1: Profil client
│   ├── document_intelligence_agent.py # Agent 2: Intelligence documentaire
│   ├── risk_assessment_agent.py       # Agent 3: Évaluation du risque
│   ├── claims_analysis_agent.py       # Agent 4: Analyse des sinistres
│   └── governance_validation_agent.py # Agent 5: Gouvernance & validation
├── orchestration/     # Orchestration LangGraph
│   ├── langgraph_orchestrator.py      # Graphe LangGraph
│   └── test_orchestrator.py           # Tests d'intégration
├── rag/               # Système RAG
│   ├── rag_system.py                  # Système RAG principal
│   └── test_rag_system.py             # Tests RAG
├── backend/          # FastAPI + moteur actuariel GLM/XGBoost
│   ├── app/
│   │   ├── actuarial/        # GLM Poisson (fréquence) + GLM Gamma (sévérité) + XGBoost
│   │   ├── agents/           # 6 agents spécialisés (LangGraph)
│   │   ├── document_engine/  # RAG TF-IDF + extraction + classification
│   │   ├── orchestrator/     # Pipeline synchrone 6 étapes
│   │   ├── api/              # REST endpoints FastAPI
│   │   └── evaluation/       # Benchmark scientifique A/B/C/D
│   └── uip_platform.db      # Base de données SQLite
└── frontend/         # Interface utilisateur React
│   └── tests/
│       └── test_full_suite.py  # 9 tests ✅
└── frontend/         # React 18 + TypeScript + Tailwind + Recharts
    └── src/
        ├── components/   # StatusBadge, AlertCard, CitationCard, AgentCard, RiskGauge, Sidebar
        └── pages/        # Dashboard, NewCase, Documents, Decision, Benchmark, Audit
```

---

## Démarrage rapide

### Backend

```bash
cd backend

# Installer les dépendances (si pas déjà fait)
pip install -r requirements.txt

# Lancer le serveur (port 8000)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Vérifier la santé
curl http://localhost:8000/api/v1/system/health
```

### Frontend

```bash
cd frontend

# Installer les dépendances (si pas déjà fait)
npm install

# Dev server avec proxy vers backend
npm run dev
# → http://localhost:5173

# Build de production
npm run build
npm run preview  # → http://localhost:4173
```

### Tests backend

```bash
cd backend
python -u tests/test_full_suite.py
# → 9/9 tests PASSED
```

---

## Fonctionnalités

### Moteur Actuariel
| Modèle | Algorithme | Usage |
|--------|-----------|-------|
| Fréquence | GLM Poisson (sklearn) | Nombre de sinistres attendus |
| Sévérité | GLM Gamma (sklearn) | Coût moyen par sinistre |
| Benchmark | XGBoost | Comparaison ML |
| Incertitude | Intervalle Poisson-Gamma composé | Intervalles de confiance |

### Pipeline Multi-Agents (6 agents)
1. **Agent Profil** — Vérification identité, cohérence âge/permis, RGPD
2. **Agent Police** — RAG réglementaire, exclusions (VTC, sport, novice)
3. **Agent Risque** — Prime pure actuarielle, tier de risque, SHAP
4. **Agent Sinistres** — Historique CRM, contradictions, résiliations antérieures
5. **Agent Intelligence Externe** — Indices territoriaux vol/accident, SRA
6. **Agent Gouvernance** — Contradictions inter-agents, biais, traçabilité

### Décision algorithmique (3 dimensions)
- **Risque actuariel** (prime pure, GLM + XGBoost)
- **Qualité documentaire** (RAG citations, extraction, cohérence)
- **Incertitude** (intervalles confiance, contradictions agents)

### Principe HITL
Aucune décision n'est définitive sans validation souscripteur humaine. Toute décision algorithmique est présentée comme recommandation.

### Audit & Conformité
- Chaîne de hachage SHA-256 sur chaque événement
- Traçabilité complète de tous les agents et décisions
- Conformité RGPD (pas de variable proxy sensible)
- Articles cités : L.211-1, L.113-8, L.113-9 Code des assurances

---

## API Reference

```
POST /api/v1/cases                    Créer un dossier
GET  /api/v1/cases                    Lister les dossiers
GET  /api/v1/cases/{id}               Détail dossier
POST /api/v1/cases/{id}/documents     Téléverser un document
POST /api/v1/cases/{id}/analyze       Lancer l'analyse multi-agents
GET  /api/v1/cases/{id}/status        Statut analyse
GET  /api/v1/cases/{id}/findings      Résultats agents
GET  /api/v1/cases/{id}/decision      Décision actuarielle
POST /api/v1/cases/{id}/review        Revue souscripteur (HITL)
GET  /api/v1/cases/{id}/audit         Piste d'audit
GET  /api/v1/benchmarks/scientific-validation  Benchmark A/B/C/D
GET  /api/v1/system/health            Santé système
GET  /api/v1/system/model-governance  Gouvernance modèles
```

Documentation interactive : http://localhost:8000/docs

---

## Benchmark Scientifique (4 configurations)

| Config | GLM Freq | GLM Sév | XGBoost | RAG | Multi-Agent |
|--------|----------|---------|---------|-----|-------------|
| A — Baseline | ✗ | ✗ | ✗ | ✗ | ✗ |
| B — GLM Only | ✓ | ✓ | ✗ | ✗ | ✗ |
| C — GLM + ML | ✓ | ✓ | ✓ | ✗ | ✗ |
| D — Full UIP  | ✓ | ✓ | ✓ | ✓ | ✓ |

Configuration D recommandée : meilleur F1, couverture citations 100%, explicabilité maximale.

---

## Conformité légale

- **L.211-1** Code des assurances — obligation d'assurance RC auto
- **L.113-8** — Nullité pour fausse déclaration intentionnelle
- **L.113-9** — Réduction proportionnelle de prime
- **R.211-1** — Réseau Bureau Central de Tarification
- **RGPD** — Pas de variable proxy discriminatoire (genre, origine)
- **Principe HITL** — Décision humaine obligatoire
