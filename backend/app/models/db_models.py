# models/db_models.py
# SQLAlchemy ORM table definitions

import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500))
    # Note: manufacturers CSV has no country column — country is on devices/events rows

    devices = relationship("Device", back_populates="manufacturer")
    features = relationship("ManufacturerFeatures", back_populates="manufacturer", uselist=False)


class ManufacturerFeatures(Base):
    """
    Precomputed manufacturer-level event aggregates.
    Populated once by scripts/seed_db.py using the same LOO logic as new_preprocessing_eda.ipynb.
    FastAPI reads these at prediction time — never recomputes per-request.
    """
    __tablename__ = "manufacturer_features"

    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), primary_key=True, index=True)
    mfr_loo_event_count = Column(Float, default=0.0)
    mfr_countries_all = Column(Float, default=1.0)
    mfr_devices_all = Column(Float, default=0.0)

    manufacturer = relationship("Manufacturer", back_populates="features")


class ClassificationFeatures(Base):
    """
    Precomputed classification-level event aggregates.
    classification_prior_count: total USA events in this classification (used as inference-time proxy).
    event_year: median event year for this classification (used as reporting-era control).
    Populated once by scripts/seed_db.py.
    """
    __tablename__ = "classification_features"

    classification = Column(String(255), primary_key=True, index=True)
    classification_prior_count = Column(Float, default=0.0)
    event_year = Column(Float, default=2010.0)


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(1000))
    classification = Column(String(255))
    description = Column(Text)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"))
    country = Column(String(100))

    manufacturer = relationship("Manufacturer", back_populates="devices")
    predictions = relationship("Prediction", back_populates="device")


class Prediction(Base):
    """Stores every inference request + result for the history dashboard."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)

    # Input fields
    input_device_name = Column(String(500), nullable=True)
    input_description = Column(Text)
    input_classification = Column(String(255))
    input_manufacturer = Column(String(500), nullable=True)
    input_known_prior_incidents = Column(Integer, nullable=True)

    # Output fields — binary failure prediction
    predicted_failure = Column(Boolean)
    predicted_label = Column(String(20))
    prob_failure = Column(Float)
    prob_no_failure = Column(Float)
    confidence = Column(Float)
    low_confidence_flag = Column(Boolean, default=False)
    escalated = Column(Boolean, default=False)
    escalation_note = Column(String(500), nullable=True)

    model_version = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())

    device = relationship("Device", back_populates="predictions")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_name = Column(String(100), unique=True)
    algorithm = Column(String(100))
    roc_auc = Column(Float)
    f1_tuned = Column(Float)
    f1_default = Column(Float)
    threshold = Column(Float)
    is_active = Column(Boolean, default=False)
    trained_at = Column(DateTime, server_default=func.now())


class DeviceRiskScore(Base):
    """Pre-computed risk score for every USA device (batch_predict.py)."""
    __tablename__ = "device_risk_scores"

    device_id = Column(Integer, ForeignKey("devices.id"), primary_key=True, index=True)
    prob_failure = Column(Float)
    predicted_failure = Column(Boolean)
    computed_at = Column(DateTime, server_default=func.now())

    device = relationship("Device", backref="risk_score")


class User(Base):
    """App users — role: 'user' (technician) or 'manufacturer'."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    role = Column(String(20))                          # 'user' | 'manufacturer'
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    manufacturer = relationship("Manufacturer", backref="user_account")


class Alert(Base):
    """High-risk prediction alert sent from technician to manufacturer."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"))
    prob_failure = Column(Float)
    predicted_label = Column(String(20))
    triggered_by = Column(String(100))                 # username of technician
    status = Column(String(20), default="unread")      # 'unread' | 'read'
    created_at = Column(DateTime, server_default=func.now())

    device = relationship("Device", backref="alerts")
    manufacturer = relationship("Manufacturer", backref="alerts")
