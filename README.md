# Medical Device Risk Predictor

Cognizant NPN AI Hackathon — Team Project

Predicts FDA risk class (I / II / III) of medical devices using machine learning trained on ICIJ Implant Files data.

---

## Problem Statement

Predict medical device failure risk class to enable proactive interventions and maintenance, using historical recall, safety alert, and field safety notice data.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| ML Training | Jupyter Notebook, scikit-learn, XGBoost |
| Backend API | FastAPI (Python) |
| Database | MySQL |
| Frontend | React |

---

## Project Structure

```
Med-Device/
├── dataset/                        # Raw CSV files (do not modify)
│   ├── devices-1681209661.csv
│   ├── events-1681209680.csv
│   └── manufacturers-1681209657.csv
│
├── notebook/                       # Jupyter ML pipeline
│   └── model_training.ipynb
│
├── backend/                        # FastAPI application
│   ├── app/
│   │   ├── main.py                 # App entry point
│   │   ├── database.py             # MySQL connection
│   │   ├── core/
│   │   │   └── config.py           # Settings / env vars
│   │   ├── models/
│   │   │   └── db_models.py        # SQLAlchemy ORM models
│   │   ├── schemas/
│   │   │   └── schemas.py          # Pydantic request/response schemas
│   │   ├── api/routes/
│   │   │   ├── predict.py          # POST /api/v1/predict
│   │   │   ├── history.py          # GET  /api/v1/predictions
│   │   │   ├── metrics.py          # GET  /api/v1/metrics
│   │   │   └── health.py           # GET  /api/v1/health
│   │   ├── services/
│   │   │   ├── prediction_service.py
│   │   │   ├── history_service.py
│   │   │   └── metrics_service.py
│   │   ├── utils/                  # Shared helpers (to be added)
│   │   └── ml/
│   │       ├── model.pkl           # Exported from notebook
│   │       └── pipeline.pkl        # Exported from notebook
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                       # React application
│   ├── public/
│   └── src/
│       ├── components/             # Reusable UI components
│       ├── pages/                  # Page-level components
│       ├── services/               # Axios API calls
│       ├── hooks/                  # Custom React hooks
│       └── utils/                  # Helper functions
│
└── docs/                           # Project documentation
    ├── api/                        # API reference
    ├── ml/                         # ML pipeline docs
    ├── database/                   # Schema docs
    └── deployment/                 # Setup and deployment guide
```

---

## Quick Start

See [docs/deployment/setup.md](docs/deployment/setup.md) for full setup instructions.

---

## Documentation Index

| Document | Location |
|----------|---------|
| API Reference | [docs/api/api_reference.md](docs/api/api_reference.md) |
| ML Pipeline | [docs/ml/ml_pipeline.md](docs/ml/ml_pipeline.md) |
| Database Schema | [docs/database/schema.md](docs/database/schema.md) |
| Setup & Deployment | [docs/deployment/setup.md](docs/deployment/setup.md) |
