# SentryMed — Medical Device Risk Predictor

Cognizant NPN AI Hackathon — Team Project

Predicts whether a USA medical device is likely to **fail** (binary: Failure / No Failure) using XGBoost trained on ICIJ Implant Files data. Technicians look up devices by ID; manufacturers receive real-time alerts when high-risk predictions are made against their devices.

---

## Problem Statement

Medical device failures cause patient harm and costly recalls. SentryMed predicts failure risk for a device at the point of assessment — before a recall occurs — using manufacturer history and device description as signals. The goal is to enable proactive risk assessment and prioritised safety interventions.

---

## Tech Stack

| Layer | Technology |
|---|---|
| ML Training | Jupyter Notebook, scikit-learn, XGBoost |
| Backend API | FastAPI (Python) |
| Database | MySQL |
| Frontend | React |
| Auth | JWT (python-jose) + bcrypt (passlib) |

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
│   │   ├── main.py                   # App entry point + CORS + router registration
│   │   ├── database.py               # SQLAlchemy engine + session
│   │   ├── core/
│   │   │   ├── config.py             # Settings from .env (DB, JWT, thresholds)
│   │   │   └── security.py           # JWT creation/decode, bcrypt, auth dependencies
│   │   ├── models/db_models.py       # ORM table definitions (9 tables)
│   │   ├── schemas/schemas.py        # Pydantic request/response schemas
│   │   ├── api/routes/
│   │   │   ├── auth.py               # POST /auth/login, GET /auth/me, GET /auth/manufacturers
│   │   │   ├── predict.py            # POST /predict — device ID lookup + ML inference + alert
│   │   │   ├── history.py            # GET /predictions — paginated history
│   │   │   ├── metrics.py            # GET /metrics[/all]
│   │   │   ├── health.py             # GET /health
│   │   │   ├── manufacturers.py      # GET /manufacturers, GET /devices
│   │   │   └── manufacturer.py       # GET /manufacturer/dashboard[/devices][/alerts]
│   │   ├── services/
│   │   │   ├── prediction_service.py # ML inference singleton (loads pkl once at startup)
│   │   │   ├── manufacturer_service.py # DB lookup for LOO features + autocomplete
│   │   │   ├── history_service.py    # Save + retrieve prediction history
│   │   │   └── metrics_service.py    # Query model_versions table
│   │   └── ml/
│   │       ├── model.pkl             # ThresholdedClassifier (XGBoost, threshold=0.42)
│   │       ├── pipeline.pkl          # ColumnTransformer (TF-IDF + OHE + Scaler)
│   │       └── model_classes.py      # ThresholdedClassifier (must match notebook version)
│   ├── scripts/
│   │   ├── seed_db.py                # Seed manufacturers, devices, features, model_versions
│   │   ├── seed_users.py             # Seed 1 technician + 3952 manufacturer accounts
│   │   └── reset_db.py               # Drop all tables and recreate
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                         # React application
│   └── src/
│       ├── components/               # ConfidenceBar, ProbabilityBars, RiskBadge, Topbar, TopFeatures
│       ├── context/AuthContext.js    # Global auth state + JWT storage
│       ├── pages/
│       │   ├── LoginPage.js          # Tab switcher: Technician / Manufacturer
│       │   ├── PredictPage.js        # Device ID lookup + prediction form
│       │   ├── HistoryPage.js        # Paginated prediction history
│       │   ├── MetricsPage.js        # Model performance dashboard
│       │   ├── HealthPage.js         # System health status
│       │   └── mfr/MfrDashboardPage.js  # Manufacturer dashboard + alerts
│       ├── services/api.js           # Axios API calls + JWT interceptor
│       └── App.js                    # Router + role-based routing
│
└── docs/
    ├── architecture.md               # System design + design decisions
    ├── roadmap.md                    # Development phases + status
    ├── presentation.md               # Presentation guide + judge Q&A
    ├── api/api_reference.md          # All endpoints documented
    ├── ml/ml_pipeline.md             # Full ML pipeline walkthrough
    ├── database/schema.md            # All tables + seeding instructions
    └── deployment/
        ├── setup.md                  # Local setup (8 steps)
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

# 4. Seed user accounts
python -m scripts.seed_users

# 5. Start backend
uvicorn app.main:app --reload --port 8000

# 6. Start frontend
cd frontend && npm install && npm start
```

---

## User Roles & Login

| Role | Username | Password | Access |
|---|---|---|---|
| Technician | `user` | `user123` | Predict, History, Metrics, Health |
| Manufacturer | `mfr_<id>` (e.g. `mfr_5247`) | `mfr123` | Manufacturer Dashboard + Alerts |

The login page has a tab switcher. Manufacturer tab shows a searchable dropdown of all 3,952 registered manufacturer accounts (first 200 shown on open, filtered as you type).

---

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/login` | None | Get JWT token |
| GET | `/api/v1/auth/me` | Any | Current user info |
| GET | `/api/v1/auth/manufacturers` | None | Manufacturer accounts for login dropdown |
| GET | `/api/v1/health` | None | Liveness + readiness check |
| POST | `/api/v1/predict` | User (optional) | Predict failure risk by device ID |
| GET | `/api/v1/predictions` | None | Paginated prediction history |
| GET | `/api/v1/metrics` | None | Active model metrics |
| GET | `/api/v1/metrics/all` | None | All model versions |
| GET | `/api/v1/manufacturers` | None | Manufacturer autocomplete |
| GET | `/api/v1/devices` | None | Device search by name or ID |
| GET | `/api/v1/manufacturer/dashboard` | Manufacturer | Stats + classification breakdown |
| GET | `/api/v1/manufacturer/devices` | Manufacturer | Paginated device list with search |
| GET | `/api/v1/manufacturer/alerts` | Manufacturer | High-risk prediction alerts |
| PATCH | `/api/v1/manufacturer/alerts/{id}/read` | Manufacturer | Mark alert as read |

Interactive docs: `http://localhost:8000/docs`

---

## Alert System

When a technician predicts a device with `prob_failure ≥ 0.42`, the system automatically creates an alert — but **only if** the device's manufacturer has a registered user account. This prevents orphan alerts for manufacturers with no login.

Manufacturers see unread alerts in their dashboard with device name, failure probability, and the technician username that triggered the prediction.

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
