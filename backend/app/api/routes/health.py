# api/routes/health.py
# GET /api/v1/health — liveness + readiness check

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.services.prediction_service import prediction_service

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    # DB check
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"

    # Model check
    model_status = "loaded" if prediction_service.model is not None else "not loaded"
    pipeline_status = "loaded" if prediction_service.pipeline is not None else "not loaded"

    overall = "ok" if db_status == "ok" and model_status == "loaded" else "degraded"

    return {
        "status": overall,
        "service": "MedDevice Risk Predictor API",
        "db": db_status,
        "model": model_status,
        "pipeline": pipeline_status,
    }
