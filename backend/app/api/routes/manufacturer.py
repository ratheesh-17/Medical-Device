# api/routes/manufacturer.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.database import get_db
from app.models.db_models import Device, Alert, ManufacturerFeatures, User
from app.core.security import require_role

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_devices: int
    total_events: int
    countries_active: int
    unread_alerts: int
    classification_breakdown: List[dict]

class DeviceRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: Optional[str] = None
    classification: Optional[str] = None
    country: Optional[str] = None

class AlertRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    device_id: int
    device_name: Optional[str] = None
    prob_failure: float
    predicted_label: str
    triggered_by: str
    status: str
    created_at: datetime


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/manufacturer/dashboard", response_model=DashboardStats)
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("manufacturer")),
):
    mfr_id = current_user.manufacturer_id

    total_devices = db.query(func.count(Device.id)).filter(Device.manufacturer_id == mfr_id).scalar() or 0

    mf = db.query(ManufacturerFeatures).filter(ManufacturerFeatures.manufacturer_id == mfr_id).first()
    total_events = int(mf.mfr_loo_event_count) if mf else 0
    countries_active = int(mf.mfr_countries_all) if mf else 0

    unread_alerts = (
        db.query(func.count(Alert.id))
        .filter(Alert.manufacturer_id == mfr_id, Alert.status == "unread")
        .scalar() or 0
    )

    # Classification breakdown
    rows = (
        db.query(Device.classification, func.count(Device.id).label("cnt"))
        .filter(Device.manufacturer_id == mfr_id)
        .group_by(Device.classification)
        .order_by(func.count(Device.id).desc())
        .limit(8)
        .all()
    )
    breakdown = [{"classification": r.classification or "Unknown", "count": r.cnt} for r in rows]

    return DashboardStats(
        total_devices=total_devices,
        total_events=total_events,
        countries_active=countries_active,
        unread_alerts=unread_alerts,
        classification_breakdown=breakdown,
    )


@router.get("/manufacturer/devices", response_model=List[DeviceRow])
def my_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    q: str = Query("", description="Search by device name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("manufacturer")),
):
    query = db.query(Device).filter(Device.manufacturer_id == current_user.manufacturer_id)
    if q.strip():
        query = query.filter(Device.name.ilike(f"%{q.strip()}%"))
    return query.order_by(Device.id).offset(skip).limit(limit).all()


@router.get("/manufacturer/alerts", response_model=List[AlertRow])
def my_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("manufacturer")),
):
    alerts = (
        db.query(Alert)
        .filter(Alert.manufacturer_id == current_user.manufacturer_id)
        .order_by(Alert.created_at.desc())
        .offset(skip).limit(limit)
        .all()
    )
    return [
        AlertRow(
            id=a.id,
            device_id=a.device_id,
            device_name=a.device.name if a.device else None,
            prob_failure=a.prob_failure,
            predicted_label=a.predicted_label,
            triggered_by=a.triggered_by,
            status=a.status,
            created_at=a.created_at,
        )
        for a in alerts
    ]


@router.patch("/manufacturer/alerts/{alert_id}/read")
def mark_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("manufacturer")),
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.manufacturer_id == current_user.manufacturer_id,
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "read"
    db.commit()
    return {"ok": True}
