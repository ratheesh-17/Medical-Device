# services/prediction_service.py
# Loads the trained pipeline + model at startup and handles inference.

import sys
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from app.core.config import settings

# Register module alias BEFORE joblib.load().
# The pkl was saved with 'model_classes' as the module path (not 'app.ml.model_classes').
import app.ml.model_classes as _model_classes_module
sys.modules.setdefault('model_classes', _model_classes_module)

from app.ml.model_classes import LabelOffsetClassifier, WeightedDecisionClassifier  # noqa: F401

CONFIDENCE_THRESHOLD = 0.60
CLASS_LABELS = {1: "I", 2: "II", 3: "III"}
TOP_N_FEATURES = 5


class PredictionService:
    def __init__(self):
        self.pipeline = None
        self.model = None
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
        print("[INFO] Model and pipeline loaded successfully.")
        # Cache feature names for explainability
        self._feature_names = self._get_feature_names()

    def _get_feature_names(self) -> list:
        """Extract feature names from the fitted ColumnTransformer pipeline."""
        if self.pipeline is None:
            return []
        try:
            names = []
            for name, transformer, cols in self.pipeline.transformers_:
                if name == "num":
                    names.extend(cols)
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
        manufacturer_name: str,
        mfr_total_events: float = 0.0,
        mfr_distinct_countries: float = 0.0,
        mfr_distinct_devices_recalled: float = 0.0,
        mfr_pct_class1_events: float = 0.0,
    ) -> dict:
        if self.pipeline is None or self.model is None:
            raise NotImplementedError(
                "Model not loaded. Run preprocessing.ipynb + model_training_v3.ipynb, "
                "then restart the server."
            )
        description_len = len(description)

        row = pd.DataFrame([{
            "description": description,
            "classification": classification,
            "description_len": description_len,
            "mfr_total_events": mfr_total_events,
            "mfr_distinct_countries": mfr_distinct_countries,
            "mfr_distinct_devices_recalled": mfr_distinct_devices_recalled,
            "mfr_pct_class1_events": mfr_pct_class1_events,
        }])

        features = self.pipeline.transform(row)
        probabilities = self.model.predict_proba(features)[0]

        # classes_ = [1, 2, 3]
        classes = self.model.classes_
        prob_dict = {CLASS_LABELS[int(c)]: round(float(p), 4) for c, p in zip(classes, probabilities)}

        predicted_label = int(self.model.predict(features)[0])
        predicted_class = CLASS_LABELS[predicted_label]
        confidence = float(probabilities[list(classes).index(predicted_label)])

        return {
            "predicted_class": predicted_class,
            "confidence": round(confidence, 4),
            "low_confidence_flag": confidence < CONFIDENCE_THRESHOLD,
            "probabilities": prob_dict,
            "top_features": self._top_features(features),
        }

    def _top_features(self, features) -> list:
        try:
            # Unwrap WeightedDecisionClassifier.base_estimator -> LabelOffsetClassifier.base_estimator_
            inner = self.model.base_estimator.base_estimator_
            importances = inner.feature_importances_
            feature_names = getattr(self, '_feature_names', [])

            if len(feature_names) != len(importances):
                return []

            feature_array = np.asarray(
                features.todense() if hasattr(features, 'todense') else features
            ).flatten()
            scores = importances * np.abs(feature_array)

            top_indices = np.argsort(scores)[::-1][:TOP_N_FEATURES]
            return [
                {'feature': feature_names[i], 'importance': round(float(scores[i]), 4)}
                for i in top_indices
                if scores[i] > 0
            ]
        except Exception:
            return []


prediction_service = PredictionService()
