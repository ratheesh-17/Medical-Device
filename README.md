# Medical Device Risk Predictor

Cognizant NPN AI Hackathon — Team Project

Predicts whether a medical device is likely to **fail** (binary: Failure / No Failure) using machine learning trained on ICIJ Implant Files data — historical recall, safety alert, and field safety notice records.

---

## Problem Statement

Medical device failures cause patient harm and costly recalls. This system predicts failure risk for a device at the point of submission — before a recall occurs — using manufacturer history and device description as signals. The goal is to enable proactive risk assessment and prioritised safety interventions.

---

## Tech Stack

| Layer | Technology |
|---|---|
| ML Training | Jupyter Notebook, scikit-learn, XGBoost |
| Backend API | FastAPI (Python) |
| Database | MySQL |
| Frontend | React |

---

## Model Performance

| Metric | Value |
|---|---|
| Test ROC-AUC | **0.8553** |
| Test F1 (tuned threshold 0.42) | **0.7528** |
| Test F1 (default threshold 0.50) | 0.7308 |
| Failure Recall (tuned) | **0.83** |
| Decision Threshold | **0.42** |

The threshold is tuned to 0.42 (vs default 0.50) to maximise Failure recall — in a safety-critical domain, missing a true failure is more costly than a false alarm.

---

## Project Structure

```
Med-Device/
├── dataset/                          # Raw CSV files (do not modify)
│   ├── devices-1681209661.csv
│   ├── events-1681209680.csv
│   └── manufacturers-1681209657.csv
│
├── notebook/                         # Jupyter ML pipeline
│   ├── new_preprocessing_eda.ipynb   # EDA + label construction + feature engineering
│   ├── model_training.ipynb          # Model selection + threshold tuning + export
│   ├── model_classes.py              # ThresholdedClassifier definition
│   └── outputs/
│       ├── model.pkl                 # Copied to backend/app/ml/
│       ├── pipeline.pkl              # Copied to backend/app/ml/
│       ├── metrics.json              # Test metrics (read by seed_db.py)
│       ├── eda_summary.json          # Dataset statistics
│       └── train.csv / test.csv      # Intermediate splits
│
├── backend/                          # FastAPI application
│   ├── app/
│   │   ├── main.py                   # App entry point + CORS
│   │   ├── database.py               # SQLAlchemy engine + session
│   │   ├── core/config.py            # Settings from .env
│   │   ├── models/db_models.py       # ORM table definitions
│   │   ├── schemas/schemas.py        # Pydantic request/response schemas
│   │   ├── api/routes/
│   │   │   ├── predict.py            # POST /api/v1/predict
│   │   │   ├── history.py            # GET  /api/v1/predictions
│   │   │   ├── metrics.py            # GET  /api/v1/metrics[/all]
│   │   │   └── health.py             # GET  /api/v1/health
│   │   ├── services/
│   │   │   ├── prediction_service.py # ML inference (loads pkl once at startup)
│   │   │   ├── manufacturer_service.py # DB lookup for LOO features
│   │   │   ├── history_service.py    # Save + retrieve prediction history
│   │   │   └── metrics_service.py    # Query model_versions table
│   │   └── ml/
│   │       ├── model.pkl             # ThresholdedClassifier (XGBoost, threshold=0.42)
│   │       ├── pipeline.pkl          # ColumnTransformer (TF-IDF + OHE + Scaler)
│   │       └── model_classes.py      # ThresholdedClassifier (must match notebook version)
│   ├── scripts/
│   │   ├── seed_db.py                # Populate manufacturers, features, model_versions
│   │   └── reset_db.py               # Drop all tables and recreate (use when schema changes)
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                         # React application
│   └── src/
│       ├── components/               # ConfidenceBar, ProbabilityBars, RiskBadge, TopFeatures
│       ├── pages/                    # PredictPage, HistoryPage, MetricsPage, HealthPage
│       ├── services/api.js           # Axios API calls
│       └── App.js
│
└── docs/
    ├── architecture.md               # System design + design decisions + alternatives
    ├── roadmap.md                    # Development phases + estimation
    ├── presentation.md               # Presentation guide + judge Q&A prep
    ├── api/api_reference.md          # All 6 endpoints documented
    ├── ml/ml_pipeline.md             # Full ML pipeline walkthrough
    ├── database/schema.md            # All 5 tables + seeding instructions
    └── deployment/
        ├── setup.md                  # Local setup (7 steps)
        └── cicd.md                   # GitHub Actions CI + AWS deployment
```

---

## Quick Start

See [docs/deployment/setup.md](docs/deployment/setup.md) for full setup instructions.

**TL;DR:**
```bash
# 1. Run notebooks (produces model.pkl + pipeline.pkl)
cd notebook && jupyter notebook
# Run: new_preprocessing_eda.ipynb → model_training.ipynb

# 2. Configure backend
cd backend && cp .env.example .env   # edit DB credentials

# 3. Seed database
python -m scripts.seed_db

# 4. Start backend
uvicorn app.main:app --reload --port 8000

# 5. Start frontend
cd frontend && npm install && npm start
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/health` | Liveness + readiness check |
| POST | `/api/v1/predict` | Predict failure risk |
| GET | `/api/v1/predictions` | Paginated prediction history |
| GET | `/api/v1/metrics` | Active model metrics |
| GET | `/api/v1/metrics/all` | All model versions |
| GET | `/api/v1/manufacturers` | Manufacturer autocomplete |

Interactive docs: `http://localhost:8000/docs`

---

## Documentation Index

| Document | Location |
|---|---|
| Architecture & Design Decisions | [docs/architecture.md](docs/architecture.md) |
| API Reference | [docs/api/api_reference.md](docs/api/api_reference.md) |
| ML Pipeline | [docs/ml/ml_pipeline.md](docs/ml/ml_pipeline.md) |
| Database Schema | [docs/database/schema.md](docs/database/schema.md) |
| Frontend | [docs/frontend/frontend.md](docs/frontend/frontend.md) |
| Setup & Deployment | [docs/deployment/setup.md](docs/deployment/setup.md) |
| CI/CD & Cloud Deployment | [docs/deployment/cicd.md](docs/deployment/cicd.md) |
| Roadmap | [docs/roadmap.md](docs/roadmap.md) |
| Presentation Guide | [docs/presentation.md](docs/presentation.md) |
