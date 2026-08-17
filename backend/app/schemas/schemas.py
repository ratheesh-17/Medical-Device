# schemas/schemas.py
# Pydantic models for request validation and response serialization

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


# ── Prediction ────────────────────────────────────────────────────────────────

class DeviceLookupRequest(BaseModel):
    device_id: int = Field(..., description="USA device ID from the ICIJ dataset")
    known_prior_incidents: Optional[int] = Field(None, ge=0, description="Technician-reported prior incidents — post-model escalation rule only.")

    model_config = ConfigDict(
        json_schema_extra={"example": {"device_id": 12345}}
    )


# Keep for history_service compatibility
class PredictRequest(BaseModel):
    device_id: int
    description: str
    classification: str
    manufacturer_name: Optional[str] = None
    device_name: Optional[str] = None
    known_prior_incidents: Optional[int] = None


class PredictResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    # Looked-up device info
    device_id: int
    device_name: Optional[str] = None
    device_description: Optional[str] = None
    device_classification: Optional[str] = None
    manufacturer_name: Optional[str] = None

    predicted_failure: bool
    predicted_label: str
    confidence: float
    low_confidence_flag: bool
    prob_failure: float
    prob_no_failure: float
    top_features: List[dict]
    model_version: str
    escalated: bool
    escalation_note: Optional[str] = None


# ── History ───────────────────────────────────────────────────────────────────

class PredictionRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    input_device_name: Optional[str] = None
    input_description: str
    input_classification: str
    input_manufacturer: Optional[str] = None
    input_known_prior_incidents: Optional[int] = None
    predicted_failure: bool
    predicted_label: str
    prob_failure: float
    prob_no_failure: float
    confidence: float
    low_confidence_flag: bool
    escalated: bool
    escalation_note: Optional[str] = None
    model_version: str
    created_at: datetime


# ── Metrics ───────────────────────────────────────────────────────────────────

class ModelMetrics(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    version_name: str
    algorithm: str
    roc_auc: float
    f1_tuned: float
    f1_default: float
    threshold: float
    trained_at: datetime


# ── Manufacturers (React dropdown) ────────────────────────────────────────────

class ManufacturerItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class DeviceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Optional[str] = None
    classification: Optional[str] = None
    country: Optional[str] = None
