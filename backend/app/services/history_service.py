# services/history_service.py
from sqlalchemy.orm import Session
from app.models.db_models import Prediction
from app.schemas.schemas import PredictRequest, PredictResponse


def save_prediction(db: Session, request: PredictRequest, response: PredictResponse) -> Prediction:
    record = Prediction(
        device_id=request.device_id,
        input_device_name=request.device_name,
        input_description=request.description,
        input_classification=request.classification,
        input_manufacturer=request.manufacturer_name,
        input_known_prior_incidents=request.known_prior_incidents,
        predicted_failure=response.predicted_failure,
        predicted_label=response.predicted_label,
        prob_failure=response.prob_failure,
        prob_no_failure=response.prob_no_failure,
        confidence=response.confidence,
        low_confidence_flag=response.low_confidence_flag,
        escalated=response.escalated,
        escalation_note=response.escalation_note,
        model_version=response.model_version,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_prediction_history(db: Session, skip: int = 0, limit: int = 50) -> list:
    return (
        db.query(Prediction)
        .order_by(Prediction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
