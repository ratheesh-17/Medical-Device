# schemas/schemas.py
# Pydantic models for request validation and response serialization

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# --- Prediction ---

class PredictRequest(BaseModel):
    description: str = Field(..., min_length=5, description="Device description")
    classification: str = Field(..., description="Device category e.g. Cardiovascular Devices")
    manufacturer_name: Optional[str] = Field(None, description="Manufacturer name")

    class Config:
        json_schema_extra = {
            "example": {
                "description": "Implantable cardiac pacemaker for rhythm management",
                "classification": "Cardiovascular Devices",
                "manufacturer_name": "Medtronic"
            }
        }


class PredictResponse(BaseModel):
    predicted_class: str
    confidence: float
    low_confidence_flag: bool
    probabilities: dict
    model_version: str


# --- History ---

class PredictionRecord(BaseModel):
    id: int
    input_description: str
    input_classification: str
    predicted_class: str
    confidence: float
    model_version: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Metrics ---

class ModelMetrics(BaseModel):
    version_name: str
    algorithm: str
    macro_f1: float
    precision_score: float
    recall_score: float
    trained_at: datetime

    class Config:
        from_attributes = True
