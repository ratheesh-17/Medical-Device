# api/routes/manufacturers.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas.schemas import ManufacturerItem, DeviceItem
from app.services.manufacturer_service import list_manufacturers
from app.models.db_models import Device
from app.database import get_db
from typing import List

router = APIRouter()


@router.get("/manufacturers", response_model=List[ManufacturerItem])
def get_manufacturers(
    q: str = Query("", description="Search query for manufacturer name"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return list_manufacturers(db, q=q, limit=limit)


@router.get("/devices", response_model=List[DeviceItem])
def search_devices(
    q: str = Query("", description="Search by device name or ID"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Device)
    if q.strip().isdigit():
        query = query.filter(Device.id == int(q.strip()))
    elif q.strip():
        query = query.filter(Device.name.ilike(f"%{q.strip()}%"))
    return query.limit(limit).all()
