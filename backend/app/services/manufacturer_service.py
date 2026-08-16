# services/manufacturer_service.py
# DB lookups for manufacturer features and the React dropdown list.

from sqlalchemy.orm import Session
from app.models.db_models import Manufacturer, ManufacturerFeatures


def get_manufacturer_features(db: Session, manufacturer_name: str) -> dict:
    """
    Look up precomputed manufacturer-level event aggregates by name.
    Returns zero-filled defaults if the manufacturer is not found.
    """
    defaults = {
        "mfr_total_events": 0.0,
        "mfr_distinct_countries": 0.0,
        "mfr_distinct_devices_recalled": 0.0,
        "mfr_pct_class1_events": 0.0,
    }

    if not manufacturer_name:
        return defaults

    mfr = (
        db.query(Manufacturer)
        .filter(Manufacturer.name.ilike(f"%{manufacturer_name}%"))
        .first()
    )
    if mfr is None or mfr.features is None:
        return defaults

    f = mfr.features
    return {
        "mfr_total_events": f.mfr_total_events or 0.0,
        "mfr_distinct_countries": f.mfr_distinct_countries or 0.0,
        "mfr_distinct_devices_recalled": f.mfr_distinct_devices_recalled or 0.0,
        "mfr_pct_class1_events": f.mfr_pct_class1_events or 0.0,
    }


def list_manufacturers(db: Session, q: str = "", limit: int = 50) -> list:
    """Return manufacturers for the React autocomplete dropdown."""
    query = db.query(Manufacturer)
    if q:
        query = query.filter(Manufacturer.name.ilike(f"%{q}%"))
    return query.order_by(Manufacturer.name).limit(limit).all()
