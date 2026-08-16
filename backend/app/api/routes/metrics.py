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
    """Merge DB model_version row with per-class data from metrics.json."""
    result = {
        "version_name": model_version.version_name,
        "algorithm": model_version.algorithm,
        "macro_f1": model_version.macro_f1,
        "precision_score": model_version.precision_score,
        "recall_score": model_version.recall_score,
        "trained_at": model_version.trained_at,
        "per_class": None,
        "class_weights": None,
    }
    if metrics_data:
        per_class_raw = metrics_data.get("test_per_class_weighted", {})
        result["per_class"] = {
            "I":   per_class_raw.get("1", {}),
            "II":  per_class_raw.get("2", {}),
            "III": per_class_raw.get("3", {}),
        }
        result["class_weights"] = metrics_data.get("class_weights", {})
    return result


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
