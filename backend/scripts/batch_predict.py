"""
scripts/batch_predict.py

Pre-computes failure risk scores for all USA devices and stores in device_risk_scores.
Run once after seed_db.py:
    python -m scripts.batch_predict
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.models.db_models import Device, DeviceRiskScore, ManufacturerFeatures, ClassificationFeatures
from app.services.prediction_service import prediction_service


def batch_predict():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        print("Loading devices...")
        devices = db.query(Device).all()
        print(f"  {len(devices)} devices found.")

        # Build lookup maps to avoid per-device DB queries
        mfr_features = {
            f.manufacturer_id: f
            for f in db.query(ManufacturerFeatures).all()
        }
        clf_features = {
            c.classification: c
            for c in db.query(ClassificationFeatures).all()
        }

        print("Clearing old scores...")
        db.query(DeviceRiskScore).delete()
        db.commit()

        print("Computing risk scores...")
        batch, total = [], len(devices)
        for i, device in enumerate(devices):
            mf = mfr_features.get(device.manufacturer_id)
            cf = clf_features.get(device.classification or "")

            try:
                result = prediction_service.predict(
                    description=device.description or "",
                    classification=device.classification or "",
                    mfr_loo_event_count=mf.mfr_loo_event_count if mf else 0.0,
                    mfr_countries_all=mf.mfr_countries_all if mf else 1.0,
                    mfr_devices_all=mf.mfr_devices_all if mf else 0.0,
                    classification_prior_count=cf.classification_prior_count if cf else 0.0,
                    event_year=cf.event_year if cf else 2010.0,
                )
                batch.append(DeviceRiskScore(
                    device_id=device.id,
                    prob_failure=result["prob_failure"],
                    predicted_failure=result["predicted_failure"],
                ))
            except Exception as e:
                print(f"  [WARN] Device {device.id} failed: {e}")

            if len(batch) >= 500:
                db.bulk_save_objects(batch)
                db.commit()
                batch = []
                print(f"  {i+1}/{total} processed...")

        if batch:
            db.bulk_save_objects(batch)
            db.commit()

        print(f"Done. {total} devices scored.")
    finally:
        db.close()


if __name__ == "__main__":
    batch_predict()
