# services/prediction_service.py
# Loads the trained pipeline + model and handles inference logic

import joblib
import numpy as np
from app.core.config import settings

CONFIDENCE_THRESHOLD = 0.60
CLASS_LABELS = {0: "I", 1: "II", 2: "III"}


class PredictionService:
    def __init__(self):
        self.pipeline = None
        self.model = None
        self._load()

    def _load(self):
        """Load pipeline and model from disk once at startup."""
        # TODO: Uncomment after notebook exports the files
        # self.pipeline = joblib.load(settings.PIPELINE_PATH)
        # self.model = joblib.load(settings.MODEL_PATH)
        pass

    def predict(self, description: str, classification: str, manufacturer_name: str) -> dict:
        """
        Transform input → run model → return prediction dict.
        TODO: Implement after pipeline.pkl and model.pkl are exported from notebook.
        """
        # features = self.pipeline.transform({
        #     "description": description,
        #     "classification": classification,
        #     "manufacturer_name": manufacturer_name,
        # })
        # probabilities = self.model.predict_proba(features)[0]
        # predicted_index = int(np.argmax(probabilities))
        # confidence = float(probabilities[predicted_index])
        # return {
        #     "predicted_class": CLASS_LABELS[predicted_index],
        #     "confidence": confidence,
        #     "low_confidence_flag": confidence < CONFIDENCE_THRESHOLD,
        #     "probabilities": {
        #         "I": round(float(probabilities[0]), 4),
        #         "II": round(float(probabilities[1]), 4),
        #         "III": round(float(probabilities[2]), 4),
        #     },
        # }
        raise NotImplementedError("Model not yet loaded. Export pipeline.pkl and model.pkl from notebook.")


prediction_service = PredictionService()
