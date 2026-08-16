# schemas/schemas.py
# Pydantic models for request validation and response serialization

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


# --- Prediction ---

class PredictRequest(BaseModel):
    description: str = Field(..., min_length=5, description="Device description")
    classification: str = Field(..., description="Device category e.g. Cardiovascular Devices")
    manufacturer_name: Optional[str] = Field(None, description="Manufacturer name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "Implantable cardiac pacemaker for rhythm management",
                "classification": "Cardiovascular Devices",
                "manufacturer_name": "Medtronic"
            }
        }
    )


class PredictResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    predicted_class: str
    confidence: float
    low_confidence_flag: bool
    probabilities: dict
    model_version: str
    top_features: list


# --- History ---

class PredictionRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    input_description: str
    input_classification: str
    input_manufacturer: Optional[str] = None
    predicted_class: str
    confidence: float
    low_confidence_flag: bool
    model_version: str
    created_at: datetime


# --- Metrics ---

class ModelMetrics(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    version_name: str
    algorithm: str
    macro_f1: float
    precision_score: float
    recall_score: float
    trained_at: datetime
    per_class: Optional[dict] = None
    class_weights: Optional[dict] = None


# --- Manufacturers (for React dropdown) ---

class ManufacturerItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
