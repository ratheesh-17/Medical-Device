# api/routes/metrics.py
# GET /api/v1/metrics — returns active model performance metrics

import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.schemas import ModelMetrics
from app.services.metrics_service import get_active_model_metrics, get_all_model_versions
from app.database import get_db
from typing import List

router = APIRouter()

METRICS_JSON = Path(__file__).parent.parent.parent.parent.parent / "notebook" / "outputs" / "metrics.json"


def _load_metrics_json() -> dict:
    if METRICS_JSON.exists():
        with open(METRICS_JSON) as f:
            return json.load(f)
    return {}


def _enrich(model_version, metrics_data: dict) -> dict:
    """Merge DB model_version row with data from metrics.json."""
    return {
        "version_name": model_version.version_name,
        "algorithm": model_version.algorithm,
        "roc_auc": model_version.roc_auc,
        "f1_tuned": model_version.f1_tuned,
        "f1_default": model_version.f1_default,
        "threshold": model_version.threshold,
        "trained_at": model_version.trained_at,
    }


@router.get("/metrics", response_model=ModelMetrics)
def get_metrics(db: Session = Depends(get_db)):
    model_version = get_active_model_metrics(db)
    if not model_version:
        raise HTTPException(status_code=404, detail="No active model found.")
    metrics_data = _load_metrics_json()
    return _enrich(model_version, metrics_data)


@router.get("/metrics/all", response_model=List[ModelMetrics])
def get_all_metrics(db: Session = Depends(get_db)):
    versions = get_all_model_versions(db)
    metrics_data = _load_metrics_json()
    return [_enrich(v, metrics_data) for v in versions]
