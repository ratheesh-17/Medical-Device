# api/routes/history.py
# GET /api/v1/predictions — returns paginated prediction history

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas.schemas import PredictionRecord
from app.services.history_service import get_prediction_history
from app.database import get_db
from typing import List

router = APIRouter()


@router.get("/predictions", response_model=List[PredictionRecord])
def get_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return get_prediction_history(db, skip=skip, limit=limit)
