# Presentation Guide

Hackathon presentation structure and talking points for each evaluation criterion.

---

## Suggested Slide Order (10–12 min)

### Slide 1 — Problem Statement (1 min)
- Medical device failures cause patient harm and costly recalls
- FDA classifies devices into 3 risk classes (I / II / III) — but classification is manual, inconsistent, and slow
- **Our solution:** Predict risk class automatically from device description + manufacturer history

**Key stat to open with:** The ICIJ Implant Files dataset covers 118,000+ devices across 60+ countries — yet 72% have no risk label. We trained on the 32,600 clean USA records.

---

### Slide 2 — Use Case & Process Flow (1 min)
- Who uses it: Regulatory analysts, procurement teams, hospital device managers
- Process: User enters device description + category → system predicts risk class in <1 second → result saved to history for audit

Show the process flow diagram from `docs/architecture.md`.

---

### Slide 3 — Architecture (1.5 min)
- React frontend → FastAPI backend → MySQL + ML model
- Highlight: ML model is loaded once at startup (not per-request) — fast inference
- Mention alternatives considered: serverless (Lambda cold start problem), microservices (overkill), PostgreSQL (MySQL sufficient)

Use the ASCII architecture diagram from `docs/architecture.md`.

---

### Slide 4 — Data & ML Pipeline (2 min)
- 3 CSVs joined: devices + events + manufacturers
- Key challenge: class imbalance (Class II = 76%)
- 3 models trained, XGBoost won CV (Macro-F1: 0.7563)
- **Innovation:** Per-class decision weights tuned on OOF predictions — no test leakage

**Metrics to highlight:**

| | Baseline | Our Model (v3) |
|--|---------|----------------|
| Macro-F1 | 0.74 | **0.80** |
| Class I Recall | 41% | **67%** |
| Class III Recall | 62% | **72%** |

---

### Slide 5 — Live Demo (2 min)
Suggested demo flow:
1. Open `http://localhost:3000`
2. Enter: *"Implantable cardiac defibrillator for ventricular arrhythmia"* / *Cardiovascular Devices*
3. Show Class III prediction with confidence score
4. Enter: *"Sterile adhesive bandage"* / *General Hospital Devices*
5. Show Class I prediction
6. Navigate to History tab — show saved predictions
7. Navigate to Metrics tab — show model performance

**If demo fails:** Show screenshots. Have `curl` commands ready as backup.

---

### Slide 6 — Innovation & Creativity (1 min)
- **Weighted decision rule:** Instead of retraining, we tune the decision boundary post-hoc on OOF predictions — elegant, no test leakage, interpretable weights
- **`WeightedDecisionClassifier`:** sklearn-compatible wrapper — drop-in replacement, works with joblib pickle, transparent to FastAPI
- **Shared `model_classes.py`:** Solves the pickle `__main__` module problem — notebook and FastAPI share the same class definitions

---

### Slide 7 — Code Quality & Best Practices (1 min)
- FastAPI with Pydantic validation, SQLAlchemy ORM, service layer separation
- Environment variables via `.env` — no hardcoded credentials
- `low_confidence_flag` in API response — system knows when it's uncertain
- Stratified CV on training set only — test set touched exactly once

---

### Slide 8 — Roadmap (1 min)
- Sprint 1: Complete integration (activate prediction service, seed DB)
- Sprint 2: Production hardening (logging, rate limiting, CI/CD)
- Sprint 3: SHAP explainability, batch prediction, CSV upload
- Long-term: Cloud deployment (AWS ECS + RDS), real-time FDA data ingestion, feedback loop for retraining

---

### Slide 9 — Team & Collaboration (30 sec)
- 8 members: 2 data, 2 ML, 2 backend, 2 frontend
- Clear ownership, parallel workstreams
- Shared `model_classes.py` as the integration contract between ML and backend teams

---

## Likely Judge Questions & Answers

**Q: Why not use a neural network / LLM for the description text?**  
A: TF-IDF + XGBoost achieves 0.80 Macro-F1 on this dataset. LLMs would add latency, cost, and deployment complexity without a clear accuracy gain at this data scale (~32k rows). It's a natural next step.

**Q: How do you handle a device description the model has never seen?**  
A: TF-IDF handles unseen terms by ignoring them (vocabulary is fixed at training time). The `low_confidence_flag` (confidence < 0.60) signals to the user when the model is uncertain.

**Q: Why not use SMOTE for class imbalance?**  
A: SMOTE generates synthetic samples in feature space — risky with TF-IDF sparse vectors. Our OOF weight tuning approach is simpler, interpretable, and achieved the same goal (Class I recall: 41% → 67%).

**Q: Is this production-ready?**  
A: The ML model and API are production-quality. The prediction service load code is written but commented out pending final pkl export. The roadmap covers the remaining steps: logging, rate limiting, CI/CD, cloud deployment.

**Q: How would you retrain the model as new recall data arrives?**  
A: Add a scheduled job that pulls new FDA recall events, appends to the training set, reruns `preprocessing.ipynb` + `model_training_v3.ipynb`, and updates the `model_versions` table. MLflow would manage artifact versioning.

---

## Key Numbers to Remember

| Metric | Value |
|--------|-------|
| Dataset size (usable) | 32,600 rows |
| Test Macro-F1 (v3) | **0.80** |
| Class I recall improvement | 41% → **67%** |
| Class III recall improvement | 62% → **72%** |
| Model size | 1.2 MB |
| API response time | < 100ms |
| Decision weights | I=1.8, II=1.0, III=2.2 |
