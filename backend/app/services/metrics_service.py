# services/metrics_service.py
# Fetches model version metrics from the database

from sqlalchemy.orm import Session
from app.models.db_models import ModelVersion


def get_active_model_metrics(db: Session) -> ModelVersion | None:
    """Return the currently active model's metrics."""
    return db.query(ModelVersion).filter(ModelVersion.is_active == True).first()


def get_all_model_versions(db: Session) -> list:
    """Return all model versions ordered by training date."""
    return db.query(ModelVersion).order_by(ModelVersion.trained_at.desc()).all()
