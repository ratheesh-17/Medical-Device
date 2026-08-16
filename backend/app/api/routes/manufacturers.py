# api/routes/manufacturers.py
# GET /api/v1/manufacturers — returns manufacturer list for the React form dropdown

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas.schemas import ManufacturerItem
from app.services.manufacturer_service import list_manufacturers
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
