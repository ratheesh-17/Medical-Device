# ml/model_classes.py
# Custom sklearn-compatible wrappers.
# Attribute names MUST match exactly what was pickled by the notebook.
# Do NOT rename attributes — pickle restores by attribute name.

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin


class LabelOffsetClassifier(BaseEstimator, ClassifierMixin):
    """
    Wraps XGBoost to handle 1-indexed labels (1,2,3) by shifting to 0-indexed internally.
    Pickle attributes: base_estimator, label_encoder_, base_estimator_, classes_
    """

    def __init__(self, base_estimator):
        self.base_estimator = base_estimator

    def fit(self, X, y, **kwargs):
        from sklearn.preprocessing import LabelEncoder
        self.label_encoder_ = LabelEncoder()
        y_enc = self.label_encoder_.fit_transform(y)
        self.base_estimator_ = self.base_estimator
        self.base_estimator_.fit(X, y_enc, **kwargs)
        self.classes_ = self.label_encoder_.classes_
        return self

    def predict(self, X):
        y_enc = self.base_estimator_.predict(X)
        return self.label_encoder_.inverse_transform(y_enc.astype(int))

    def predict_proba(self, X):
        return self.base_estimator_.predict_proba(X)


class WeightedDecisionClassifier(BaseEstimator, ClassifierMixin):
    """
    Applies per-class decision weights at inference:
      predicted_class = argmax(predict_proba(X) * class_weights)
    predict_proba() returns true unweighted probabilities.
    Pickle attributes: base_estimator, class_weights, classes_order, classes_
    """

    def __init__(self, base_estimator, class_weights, classes_order):
        self.base_estimator = base_estimator
        self.class_weights = class_weights    # list e.g. [1.8, 1.0, 2.2]
        self.classes_order = classes_order    # list e.g. [1, 2, 3]
        self.classes_ = np.array(classes_order)

    def predict_proba(self, X):
        return self.base_estimator.predict_proba(X)

    def predict(self, X):
        proba = self.predict_proba(X)
        weights = np.array(self.class_weights)
        weighted = proba * weights
        indices = np.argmax(weighted, axis=1)
        return self.classes_[indices]
