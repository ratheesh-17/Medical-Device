# services/manufacturer_service.py
# DB lookups for manufacturer features, classification features, and the React dropdown list.

import datetime
from sqlalchemy.orm import Session
from app.models.db_models import Manufacturer, ManufacturerFeatures, ClassificationFeatures


def get_manufacturer_features(db: Session, manufacturer_name: str) -> dict:
    """
    Look up precomputed manufacturer-level LOO event aggregates by name.
    Returns zero-filled defaults if the manufacturer is not found.
    """
    defaults = {
        "mfr_loo_event_count": 0.0,
        "mfr_countries_all": 1.0,
        "mfr_devices_all": 0.0,
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
        "mfr_loo_event_count": f.mfr_loo_event_count or 0.0,
        "mfr_countries_all": f.mfr_countries_all or 1.0,
        "mfr_devices_all": f.mfr_devices_all or 0.0,
    }


def get_classification_features(db: Session, classification: str) -> dict:
    """
    Look up precomputed classification-level features.

    classification_prior_count: total USA events in this classification.
      At inference time for a new device, we use the stored total as a proxy
      (the device has no prior events to exclude).

    event_year: median event year for this classification.
      Controls for the reporting-era confound (failure rate jumped 2%->30%
      between 2005-2009 as the reporting system matured).
      For a new device being submitted today, we use the current year.
    """
    current_year = float(datetime.datetime.now().year)

    defaults = {
        "classification_prior_count": 0.0,
        "event_year": current_year,
    }

    if not classification:
        return defaults

    row = (
        db.query(ClassificationFeatures)
        .filter(ClassificationFeatures.classification == classification)
        .first()
    )
    if row is None:
        return defaults

    return {
        "classification_prior_count": row.classification_prior_count or 0.0,
        "event_year": current_year,  # always use current year for new submissions
    }


def list_manufacturers(db: Session, q: str = "", limit: int = 50) -> list:
    """Return manufacturers for the React autocomplete dropdown."""
    query = db.query(Manufacturer)
    if q:
        query = query.filter(Manufacturer.name.ilike(f"%{q}%"))
    return query.order_by(Manufacturer.name).limit(limit).all()
