# api/routes/metrics.py
# GET /api/v1/metrics — returns active model performance metrics

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.schemas import ModelMetrics
from app.services.metrics_service import get_active_model_metrics, get_all_model_versions
from app.database import get_db
from typing import List

router = APIRouter()


@router.get("/metrics", response_model=ModelMetrics)
def get_metrics(db: Session = Depends(get_db)):
    metrics = get_active_model_metrics(db)
    if not metrics:
        raise HTTPException(status_code=404, detail="No active model found.")
    return metrics


@router.get("/metrics/all", response_model=List[ModelMetrics])
def get_all_metrics(db: Session = Depends(get_db)):
    return get_all_model_versions(db)
