# api/routes/health.py
# GET /api/v1/health — simple liveness check

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "MedDevice Risk Predictor API"}
