"""
scripts/seed_db.py

Loads the raw ICIJ Implant Files CSVs into MySQL and computes the
manufacturer_features table using the same aggregation logic as
preprocessing.ipynb.

Run from the backend/ directory:
    python -m scripts.seed_db

Requires:
    - .env file with DB credentials
    - dataset/ CSVs at ../../dataset/ relative to this file
"""

import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path
from sqlalchemy.orm import Session

# Allow running as `python -m scripts.seed_db` from backend/
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, Base, SessionLocal
from app.models.db_models import (
    Manufacturer, ManufacturerFeatures, Device, Event, ModelVersion
)
from app.core.config import settings

DATASET_DIR = Path(__file__).parent.parent.parent / "dataset"
METRICS_JSON = Path(__file__).parent.parent.parent / "notebook" / "outputs" / "metrics.json"


def normalize_action_class(x):
    if pd.isna(x):
        return np.nan
    x = str(x).strip().lower()
    if x in ("1", "i", "class 1", "class i"):
        return "I"
    if x in ("2", "ii", "class 2", "class ii"):
        return "II"
    if x in ("3", "iii", "class 3", "class iii"):
        return "III"
    return np.nan


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

        # ── 2. Seed manufacturers ─────────────────────────────────────────────
        print("Seeding manufacturers...")
        db.query(ManufacturerFeatures).delete()
        db.query(Manufacturer).delete()
        db.commit()

        mfr_records = []
        for _, row in manufacturers_df.iterrows():
            mfr_records.append(Manufacturer(
                id=int(row["id"]),
                name=str(row.get("name", "") or ""),
                country=str(row.get("country", "") or ""),
            ))
        db.bulk_save_objects(mfr_records)
        db.commit()
        print(f"  Inserted {len(mfr_records)} manufacturers.")

        # ── 3. Compute manufacturer_features (same logic as preprocessing.ipynb) ──
        print("Computing manufacturer_features...")
        events_with_mfr = events_df.merge(
            devices_df[["id", "manufacturer_id"]].rename(columns={"id": "device_id"}),
            on="device_id",
            how="left",
        )

        mfr_agg = events_with_mfr.groupby("manufacturer_id").agg(
            mfr_total_events=("id", "count"),
            mfr_distinct_countries=("country", "nunique"),
            mfr_distinct_devices_recalled=("device_id", "nunique"),
        ).reset_index()

        events_with_mfr["action_class_norm"] = events_with_mfr["action_classification"].apply(
            normalize_action_class
        )
        severity_share = (
            events_with_mfr.groupby("manufacturer_id")["action_class_norm"]
            .apply(lambda s: (s == "I").mean())
            .reset_index(name="mfr_pct_class1_events")
        )
        mfr_features_df = mfr_agg.merge(severity_share, on="manufacturer_id", how="left")
        mfr_features_df["mfr_pct_class1_events"] = mfr_features_df["mfr_pct_class1_events"].fillna(0.0)

        feat_records = []
        for _, row in mfr_features_df.iterrows():
            feat_records.append(ManufacturerFeatures(
                manufacturer_id=int(row["manufacturer_id"]),
                mfr_total_events=float(row["mfr_total_events"]),
                mfr_distinct_countries=float(row["mfr_distinct_countries"]),
                mfr_distinct_devices_recalled=float(row["mfr_distinct_devices_recalled"]),
                mfr_pct_class1_events=float(row["mfr_pct_class1_events"]),
            ))
        db.bulk_save_objects(feat_records)
        db.commit()
        print(f"  Inserted {len(feat_records)} manufacturer_features rows.")

        # ── 4. Seed model_versions from metrics.json ──────────────────────────
        if METRICS_JSON.exists():
            import json
            print("Seeding model_versions from metrics.json...")
            with open(METRICS_JSON) as f:
                m = json.load(f)

            db.query(ModelVersion).delete()
            db.commit()

            mv = ModelVersion(
                version_name="xgboost_v3_weighted",
                algorithm=f"{m.get('selected_model', 'XGBoost')} + WeightedDecisionClassifier",
                macro_f1=m.get("test_macro_f1_weighted_final", 0.0),
                precision_score=m.get("test_per_class_weighted", {}).get("2", {}).get("precision", 0.0),
                recall_score=m.get("test_per_class_weighted", {}).get("2", {}).get("recall", 0.0),
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
