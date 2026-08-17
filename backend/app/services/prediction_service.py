# services/prediction_service.py
# Loads the trained pipeline + model at startup and handles inference.

import sys
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from app.core.config import settings

# Register module alias BEFORE joblib.load() so pickle can find ThresholdedClassifier.
import app.ml.model_classes as _model_classes_module
sys.modules.setdefault("model_classes", _model_classes_module)

from app.ml.model_classes import ThresholdedClassifier  # noqa: F401

CONFIDENCE_THRESHOLD = 0.60

# Feature columns expected by the preprocessor (must match new_preprocessing_eda.ipynb v3)
FEATURE_COLS = [
    "classification",
    "description",
    "mfr_loo_event_count",
    "mfr_countries_all",
    "mfr_devices_all",
    "description_len",
    "classification_prior_count",
    "event_year",
]

TOP_N_FEATURES = 5

# Post-model escalation rule:
# If the technician reports >= this many prior incidents AND the model already
# flags elevated risk (prob_failure >= ESCALATION_PROB_THRESHOLD), escalate.
# This is a documented business rule, NOT a learned model weight.
# Rationale: per-device incident history showed no learnable pattern in training data
# (only 1.7% of devices have >1 event, severity stays flat). Rule is applied transparently.
ESCALATION_INCIDENT_THRESHOLD = 2
ESCALATION_PROB_THRESHOLD = 0.30  # model must already show some elevated risk


class PredictionService:
    def __init__(self):
        self.pipeline = None
        self.model = None
        self._feature_names: list = []
        self._load()

    def _load(self):
        """Load pipeline and model from disk once at startup. Fails gracefully if files missing."""
        pipeline_path = Path(settings.PIPELINE_PATH)
        model_path = Path(settings.MODEL_PATH)

        if not pipeline_path.exists() or not model_path.exists():
            print(
                f"[WARNING] Model files not found ({settings.MODEL_PATH}, {settings.PIPELINE_PATH}). "
                "Run the notebooks first, then restart the server."
            )
            return

        self.pipeline = joblib.load(pipeline_path)
        self.model = joblib.load(model_path)
        self._feature_names = self._get_feature_names()
        print("[INFO] Model and pipeline loaded successfully.")

    def _get_feature_names(self) -> list:
        """Extract feature names from the fitted ColumnTransformer pipeline."""
        if self.pipeline is None:
            return []
        try:
            names = []
            for name, transformer, cols in self.pipeline.transformers_:
                if name == "num":
                    names.extend(cols if isinstance(cols, list) else [cols])
                elif name == "cat":
                    names.extend(transformer.get_feature_names_out(cols).tolist())
                elif name == "text":
                    names.extend(transformer.get_feature_names_out().tolist())
            return names
        except Exception:
            return []

    def predict(
        self,
        description: str,
        classification: str,
        mfr_loo_event_count: float = 0.0,
        mfr_countries_all: float = 1.0,
        mfr_devices_all: float = 0.0,
        classification_prior_count: float = 0.0,
        event_year: float = 2010.0,
        known_prior_incidents: int = None,
    ) -> dict:
        if self.pipeline is None or self.model is None:
            raise NotImplementedError(
                "Model not loaded. Run new_preprocessing_eda.ipynb + model_training.ipynb, "
                "then restart the server."
            )

        row = pd.DataFrame([{
            "description": description,
            "classification": classification,
            "mfr_loo_event_count": mfr_loo_event_count,
            "mfr_countries_all": mfr_countries_all,
            "mfr_devices_all": mfr_devices_all,
            "description_len": len(description),
            "classification_prior_count": classification_prior_count,
            "event_year": event_year,
        }])

        features = self.pipeline.transform(row)
        proba = self.model.predict_proba(features)[0]  # [P(no_failure), P(failure)]
        predicted_label = int(self.model.predict(features)[0])

        prob_failure = float(proba[1])
        prob_no_failure = float(proba[0])
        confidence = prob_failure if predicted_label == 1 else prob_no_failure

        # Post-model escalation rule (transparent business rule, not learned weight)
        escalated = False
        escalation_note = None
        if (
            known_prior_incidents is not None
            and known_prior_incidents >= ESCALATION_INCIDENT_THRESHOLD
            and prob_failure >= ESCALATION_PROB_THRESHOLD
        ):
            escalated = True
            escalation_note = (
                f"Escalated: model shows elevated risk (P(failure)={prob_failure:.2f}) "
                f"and technician reported {known_prior_incidents} prior incident(s) for this device. "
                f"Rule threshold: >={ESCALATION_INCIDENT_THRESHOLD} incidents + "
                f"P(failure)>={ESCALATION_PROB_THRESHOLD}."
            )
            # If not already predicted as failure, override label
            if predicted_label == 0:
                predicted_label = 1

        return {
            "predicted_failure": bool(predicted_label),
            "predicted_label": "Failure" if predicted_label == 1 else "No Failure",
            "confidence": round(confidence, 4),
            "low_confidence_flag": confidence < CONFIDENCE_THRESHOLD,
            "prob_failure": round(prob_failure, 4),
            "prob_no_failure": round(prob_no_failure, 4),
            "top_features": self._top_features(features),
            "escalated": escalated,
            "escalation_note": escalation_note,
        }

    def _top_features(self, features) -> list:
        try:
            inner = self.model.base_estimator
            importances = inner.feature_importances_
            if len(self._feature_names) != len(importances):
                return []
            feature_array = np.asarray(
                features.todense() if hasattr(features, "todense") else features
            ).flatten()
            scores = importances * np.abs(feature_array)
            top_indices = np.argsort(scores)[::-1][:TOP_N_FEATURES]
            return [
                {"feature": self._feature_names[i], "importance": round(float(scores[i]), 4)}
                for i in top_indices
                if scores[i] > 0
            ]
        except Exception:
            return []


prediction_service = PredictionService()
