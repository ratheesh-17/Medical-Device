# services/history_service.py
# Database operations for prediction history

from sqlalchemy.orm import Session
from app.models.db_models import Prediction
from app.schemas.schemas import PredictRequest, PredictResponse


def save_prediction(db: Session, request: PredictRequest, response: PredictResponse) -> Prediction:
    """Persist a prediction result to the DB."""
    record = Prediction(
        input_description=request.description,
        input_classification=request.classification,
        input_manufacturer=request.manufacturer_name,
        predicted_class=response.predicted_class,
        prob_class_1=response.probabilities.get("I"),
        prob_class_2=response.probabilities.get("II"),
        prob_class_3=response.probabilities.get("III"),
        confidence=response.confidence,
        low_confidence_flag=response.low_confidence_flag,
        model_version=response.model_version,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_prediction_history(db: Session, skip: int = 0, limit: int = 50) -> list:
    """Fetch paginated prediction history."""
    return (
        db.query(Prediction)
        .order_by(Prediction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
