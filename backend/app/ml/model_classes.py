"""Shared model classes -- see notebook v3 for why this must be a real, separately
importable module rather than defined inline (pickling/unpickling across processes)."""
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin


class ThresholdedClassifier(BaseEstimator, ClassifierMixin):
    """Wraps a fitted probabilistic binary classifier; applies a tuned decision threshold.

    predict()       -> 1 if predict_proba()[:,1] >= threshold else 0   (the corrected decision)
    predict_proba() -> the base estimator's true probabilities          (for a genuine confidence score)
    """
    def __init__(self, base_estimator=None, threshold=0.5):
        self.base_estimator = base_estimator
        self.threshold = threshold

    def fit(self, X, y):
        self.classes_ = np.array([0, 1])
        return self

    def predict(self, X):
        proba = self.base_estimator.predict_proba(X)[:, 1]
        return (proba >= self.threshold).astype(int)

    def predict_proba(self, X):
        return self.base_estimator.predict_proba(X)
