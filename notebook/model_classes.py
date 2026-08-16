"""
Shared model class definitions.

CRITICAL: these classes must be importable from the *exact same module path* in both
the training notebook and the FastAPI backend. joblib/pickle serialize a reference to
the class's module + name, not the class's code -- if the module path differs between
where a model was saved and where it's loaded, unpickling fails with:

    AttributeError: Can't get attribute 'ClassName' on <module '...'>

This file is the single source of truth. Both sides import from it by the same name:
    from model_classes import LabelOffsetClassifier, WeightedDecisionClassifier
(with this file's directory on sys.path) -- never redefine these classes inline
in a notebook cell or elsewhere, or pickled models trained against that copy will
only load in the process that defined it.
"""
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.preprocessing import LabelEncoder


class LabelOffsetClassifier(BaseEstimator, ClassifierMixin):
    """Wraps an estimator that needs 0-indexed labels (e.g. XGBoost); exposes
    original-label predict/predict_proba. Subclasses BaseEstimator/ClassifierMixin
    so it works correctly with cross_val_score/cross_val_predict, which need to
    clone() estimators internally.
    """
    def __init__(self, base_estimator=None):
        self.base_estimator = base_estimator

    def fit(self, X, y, **fit_params):
        self.label_encoder_ = LabelEncoder()
        y_enc = self.label_encoder_.fit_transform(y)
        self.base_estimator_ = clone(self.base_estimator)
        self.base_estimator_.fit(X, y_enc, **fit_params)
        self.classes_ = self.label_encoder_.classes_  # original labels, sorted
        return self

    def predict(self, X):
        return self.label_encoder_.inverse_transform(self.base_estimator_.predict(X))

    def predict_proba(self, X):
        return self.base_estimator_.predict_proba(X)


class WeightedDecisionClassifier(BaseEstimator, ClassifierMixin):
    """Wraps a fitted probabilistic classifier; applies per-class decision weights
    at predict time to correct for majority-class bias under class imbalance.

    predict()       -> argmax(predict_proba() * class_weights)   (the corrected decision)
    predict_proba() -> the base estimator's true probabilities   (for a genuine confidence score)
    """
    def __init__(self, base_estimator=None, class_weights=None, classes_order=None):
        self.base_estimator = base_estimator
        self.class_weights = class_weights
        self.classes_order = classes_order

    def fit(self, X, y):
        # base_estimator is expected to already be fitted separately -- this keeps the
        # "fit the model" and "tune the decision rule" stages clearly distinct.
        self.classes_ = np.array(self.classes_order)
        return self

    def predict(self, X):
        proba = self.base_estimator.predict_proba(X)
        weighted = proba * np.array(self.class_weights)
        return self.classes_[weighted.argmax(axis=1)]

    def predict_proba(self, X):
        return self.base_estimator.predict_proba(X)
