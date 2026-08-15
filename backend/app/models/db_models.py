# models/db_models.py
# SQLAlchemy ORM table definitions

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500))
    classification = Column(String(255))
    description = Column(Text)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"))
    risk_class = Column(String(10))
    implanted = Column(String(10))
    country = Column(String(100))

    manufacturer = relationship("Manufacturer", back_populates="devices")
    events = relationship("Event", back_populates="device")
    predictions = relationship("Prediction", back_populates="device")


class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500))
    country = Column(String(100))

    devices = relationship("Device", back_populates="manufacturer")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    action = Column(Text)
    action_classification = Column(String(50))
    action_level = Column(String(100))
    country = Column(String(100))
    event_date = Column(DateTime)

    device = relationship("Device", back_populates="events")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    input_description = Column(Text)
    input_classification = Column(String(255))
    input_manufacturer = Column(String(500))
    predicted_class = Column(String(10))
    prob_class_1 = Column(Float)
    prob_class_2 = Column(Float)
    prob_class_3 = Column(Float)
    confidence = Column(Float)
    low_confidence_flag = Column(Boolean, default=False)
    model_version = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())

    device = relationship("Device", back_populates="predictions")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_name = Column(String(100), unique=True)
    algorithm = Column(String(100))
    macro_f1 = Column(Float)
    precision_score = Column(Float)
    recall_score = Column(Float)
    is_active = Column(Boolean, default=False)
    trained_at = Column(DateTime, server_default=func.now())
