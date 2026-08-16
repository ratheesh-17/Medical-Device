# ML Pipeline Documentation

## Overview

Supervised multi-class classification to predict FDA risk class (I / II / III) of medical devices, trained on ICIJ Implant Files data.

---

## Dataset

| File | Rows | Role |
|------|------|------|
| devices-1681209661.csv | 118,249 | Main dataset — contains target `risk_class` |
| events-1681209680.csv | 124,969 | Recall/safety events — linked via `device_id` |
| manufacturers-1681209657.csv | 32,531 | Manufacturer info — linked via `manufacturer_id` |

---

## Key Data Findings

- `risk_class` is missing in 72% of rows
- Clean labels (1, 2, 3) exist only for USA records → **~32,600 usable labeled rows**
- Class imbalance: Class II ≈ 76%, Class I ≈ 17%, Class III ≈ 7%
- `action_classification` in events.csv is recall severity — a different signal from device risk class

---

## Notebooks

| Notebook | Purpose |
|----------|---------|
| `preprocessing.ipynb` | EDA, cleaning, feature engineering → outputs `train.csv`, `test.csv`, `preprocessor.pkl` |
| `model_training_v3.ipynb` | Model training, CV selection, weight tuning → outputs `model.pkl`, `pipeline.pkl` |

---

## Pipeline Steps

### 1. Data Cleaning (`preprocessing.ipynb`)
- Filter `risk_class` to clean values: 1, 2, 3 (USA records only)
- Normalize `action_classification` inconsistent formats (Class 2 / II / 2 → 2)
- Handle missing values per-column strategy

### 2. Data Integration
- Join devices ← events (aggregate per manufacturer, not row-duplicate)
- Join devices ← manufacturers

### 3. Feature Engineering

| Feature Group | Features |
|--------------|---------|
| Device | `classification`, description length, `implanted` flag |
| Text (NLP) | TF-IDF on `description` (top N terms) |
| Manufacturer | total recall count, distinct countries, repeat-offender flag |

> **Data leakage rule:** Only manufacturer-level aggregates across *other* devices are used — never the device's own event count.

### 4. Train / Test Split
- 80% train / 20% test, stratified by class

### 5. Models Trained

| Model | CV Macro-F1 (mean ± std) |
|-------|--------------------------|
| Logistic Regression | 0.6727 ± 0.0044 |
| Random Forest | 0.7115 ± 0.0072 |
| **XGBoost** *(selected)* | **0.7563 ± 0.0071** |

- 5-fold stratified CV on training set only — test set touched exactly once
- XGBoost wrapped in `LabelOffsetClassifier` (handles 0-indexed labels internally)
- RF size capped via `max_depth=18`, `min_samples_leaf=3`

### 6. Class Imbalance Handling — Weighted Decision Rule

Default argmax over-predicts Class II (76% of data). A per-class decision weight is applied at inference:

```
predicted_class = argmax(predict_proba(X) * class_weights)
```

| Class | Weight | Effect |
|-------|--------|--------|
| I | 1.8 | Boosts recall for low-risk devices |
| II | 1.0 | Neutral (majority class) |
| III | 2.2 | Boosts recall for high-risk devices |

Weights were tuned via grid search on OOF (out-of-fold) predictions from the training set only — **no test leakage**.

The final model is wrapped in `WeightedDecisionClassifier`:
- `.predict()` uses weighted argmax
- `.predict_proba()` returns true unweighted probabilities (honest confidence scores in UI)

Both classes (`LabelOffsetClassifier`, `WeightedDecisionClassifier`) are defined in `backend/app/ml/model_classes.py` — **not inline in the notebook** — to ensure pickle compatibility with FastAPI.

### 7. Evaluation Metrics

**Primary metric:** Macro-F1 (handles class imbalance)

| Metric | Baseline (argmax) | v3 (weighted) |
|--------|-------------------|---------------|
| Test Macro-F1 | 0.7426 | **0.8014** |
| OOF Macro-F1 | 0.7565 | **0.8071** |

**Per-class test results (v3 weighted):**

| Class | Precision | Recall | F1 |
|-------|-----------|--------|----|
| I | 0.714 | 0.669 | 0.691 |
| II | 0.904 | 0.934 | 0.919 |
| III | 0.892 | 0.716 | 0.795 |

Class I recall improved from **41% → 67%**, Class III recall from **62% → 72%**.

Model size: **1.2 MB**

### 8. Export

```python
# preprocessing.ipynb
joblib.dump(preprocessor, "outputs/preprocessor.pkl")
shutil.copy("outputs/preprocessor.pkl", "../backend/app/ml/pipeline.pkl")

# model_training_v3.ipynb
joblib.dump(best_model_weighted, "outputs/model.pkl")
joblib.dump(best_model_weighted, "../backend/app/ml/model.pkl")
joblib.dump(preprocessor, "outputs/pipeline.pkl")
joblib.dump(preprocessor, "../backend/app/ml/pipeline.pkl")
```

- `pipeline.pkl` — fitted preprocessor (TF-IDF + OHE + scaler). Fit **only on X_train**, never refit at inference.
- `model.pkl` — `WeightedDecisionClassifier` wrapping XGBoost. `predict_proba` columns → classes `[1, 2, 3]`.

---

## Inference Flow

```
User Input (description + classification + manufacturer_name)
    ↓
pipeline.pkl  →  transform features
    ↓
model.pkl  →  predict_proba  →  weighted argmax
    ↓
{ predicted_class, confidence, probabilities }
```

---

## Model Versioning

Each trained model is recorded in the `model_versions` DB table with Macro-F1, precision, recall, and an `is_active` flag. The active model's metrics are served via `GET /api/v1/metrics`.
