"""
scripts/seed_db.py

Loads the raw ICIJ Implant Files CSVs into MySQL and computes the
manufacturer_features and classification_features tables.

Run from the backend/ directory:
    python -m scripts.seed_db

Requires:
    - .env file with DB credentials
    - dataset/ CSVs at ../../dataset/ relative to this file
    - notebook/outputs/metrics.json (produced by model_training.ipynb)
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, Base, SessionLocal
from app.models.db_models import (
    Manufacturer, ManufacturerFeatures, ClassificationFeatures,
    Device, ModelVersion,
)

DATASET_DIR = Path(__file__).parent.parent.parent / "dataset"
METRICS_JSON = Path(__file__).parent.parent.parent / "notebook" / "outputs" / "metrics.json"


def seed():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # ── 1. Load CSVs ──────────────────────────────────────────────────────
        print("Loading CSVs...")
        devices_df = pd.read_csv(DATASET_DIR / "devices-1681209661.csv", low_memory=False)
        events_df = pd.read_csv(DATASET_DIR / "events-1681209680.csv", low_memory=False)
        manufacturers_df = pd.read_csv(DATASET_DIR / "manufacturers-1681209657.csv", low_memory=False)
        print(f"  devices: {devices_df.shape}, events: {events_df.shape}, manufacturers: {manufacturers_df.shape}")

        # ── 2. USA-only filter ────────────────────────────────────────────────
        usa_device_ids = set(
            events_df.dropna(subset=["action_classification", "determined_cause"])["device_id"].unique()
        )
        devices_usa = devices_df[devices_df["id"].isin(usa_device_ids)]
        events_usa = events_df[events_df["device_id"].isin(usa_device_ids)]
        print(f"  USA-only: {len(devices_usa)} devices, {len(events_usa)} events")

        # ── 3. Seed manufacturers ─────────────────────────────────────────────
        print("Seeding manufacturers...")
        from app.models.db_models import Prediction
        db.query(Prediction).delete()
        db.query(Device).delete()
        db.query(ManufacturerFeatures).delete()
        db.query(Manufacturer).delete()
        db.commit()

        mfr_records = [
            Manufacturer(
                id=int(row["id"]),
                name=str(row.get("name", "") or ""),
            )
            for _, row in manufacturers_df.iterrows()
        ]
        db.bulk_save_objects(mfr_records)
        db.commit()
        print(f"  Inserted {len(mfr_records)} manufacturers.")

        # ── 4. Compute manufacturer_features (LOO) ────────────────────────────
        print("Computing manufacturer_features (LOO)...")
        events_with_mfr = events_usa.merge(
            devices_usa[["id", "manufacturer_id"]].rename(columns={"id": "device_id"}),
            on="device_id",
            how="left",
        )

        mfr_total = (
            events_with_mfr.groupby("manufacturer_id")["id"]
            .count()
            .reset_index(name="mfr_total_events")
        )
        mfr_countries = (
            events_with_mfr.groupby("manufacturer_id")["country"]
            .nunique()
            .reset_index(name="mfr_countries_all")
        )
        mfr_devices = (
            events_with_mfr.groupby("manufacturer_id")["device_id"]
            .nunique()
            .reset_index(name="mfr_devices_all")
        )

        mfr_features_df = (
            mfr_total
            .merge(mfr_countries, on="manufacturer_id", how="left")
            .merge(mfr_devices, on="manufacturer_id", how="left")
        )
        mfr_features_df["mfr_loo_event_count"] = mfr_features_df["mfr_total_events"].astype(float)
        mfr_features_df["mfr_countries_all"] = mfr_features_df["mfr_countries_all"].fillna(1.0).astype(float)
        mfr_features_df["mfr_devices_all"] = mfr_features_df["mfr_devices_all"].fillna(0.0).astype(float)

        feat_records = [
            ManufacturerFeatures(
                manufacturer_id=int(row["manufacturer_id"]),
                mfr_loo_event_count=float(row["mfr_loo_event_count"]),
                mfr_countries_all=float(row["mfr_countries_all"]),
                mfr_devices_all=float(row["mfr_devices_all"]),
            )
            for _, row in mfr_features_df.iterrows()
        ]
        db.bulk_save_objects(feat_records)
        db.commit()
        print(f"  Inserted {len(feat_records)} manufacturer_features rows.")

        # ── 5. Compute classification_features ────────────────────────────────
        print("Computing classification_features...")
        db.query(ClassificationFeatures).delete()
        db.commit()

        # Join events with device classification
        events_with_class = events_usa.merge(
            devices_usa[["id", "classification"]].rename(columns={"id": "device_id"}),
            on="device_id",
            how="left",
        )
        events_with_class["classification"] = events_with_class["classification"].fillna("Unknown")

        # Total event count per classification (used as classification_prior_count proxy at inference)
        clf_counts = (
            events_with_class.groupby("classification")
            .size()
            .reset_index(name="classification_prior_count")
        )

        # Median event year per classification (for reporting-era control)
        events_with_class["create_date_parsed"] = pd.to_datetime(
            events_with_class["create_date"], errors="coerce"
        )
        clf_years = (
            events_with_class.groupby("classification")["create_date_parsed"]
            .apply(lambda x: float(x.dt.year.median()))
            .reset_index(name="event_year")
        )

        clf_features_df = clf_counts.merge(clf_years, on="classification", how="left")
        clf_features_df["event_year"] = clf_features_df["event_year"].fillna(2010.0)

        clf_records = [
            ClassificationFeatures(
                classification=str(row["classification"]),
                classification_prior_count=float(row["classification_prior_count"]),
                event_year=float(row["event_year"]),
            )
            for _, row in clf_features_df.iterrows()
        ]
        db.bulk_save_objects(clf_records)
        db.commit()
        print(f"  Inserted {len(clf_records)} classification_features rows.")

        # ── 6. Seed devices (USA only) ──────────────────────────────────────
        print("Seeding devices (USA only)...")
        device_country = (
            events_usa.groupby("device_id")["country"]
            .first()
            .reset_index()
            .rename(columns={"device_id": "id"})
        )
        devices_to_seed = devices_usa.merge(device_country, on="id", how="left")

        device_records = [
            Device(
                id=int(row["id"]),
                name=str(row.get("name", "") or "")[:1000],
                classification=str(row.get("classification", "") or "")[:255],
                description=str(row.get("description", "") or ""),
                manufacturer_id=int(row["manufacturer_id"]) if pd.notna(row.get("manufacturer_id")) else None,
                country=str(row.get("country", "") or "")[:100],
            )
            for _, row in devices_to_seed.iterrows()
        ]
        db.bulk_save_objects(device_records)
        db.commit()
        print(f"  Inserted {len(device_records)} devices.")

        # ── 7. Seed model_versions from metrics.json ──────────────────────────
        if METRICS_JSON.exists():
            print("Seeding model_versions from metrics.json...")
            with open(METRICS_JSON) as f:
                m = json.load(f)

            db.query(ModelVersion).delete()
            db.commit()

            mv = ModelVersion(
                version_name="xgboost_binary_v2",
                algorithm=f"{m.get('selected_model', 'XGBoost')} + ThresholdedClassifier",
                roc_auc=m.get("test_roc_auc", 0.0),
                f1_tuned=m.get("test_f1_tuned_threshold", 0.0),
                f1_default=m.get("test_f1_default_threshold", 0.0),
                threshold=m.get("decision_threshold", 0.5),
                is_active=True,
            )
            db.add(mv)
            db.commit()
            print("  model_versions seeded.")
        else:
            print(f"  metrics.json not found at {METRICS_JSON}, skipping model_versions seed.")

        print("Done.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
