# ML Pipeline Documentation

## Overview

Supervised multi-class classification to predict FDA risk class (I / II / III) of medical devices.

---

## Dataset

| File | Rows | Role |
|------|------|------|
| devices.csv | 118,249 | Main dataset — contains target `risk_class` |
| events.csv | 124,969 | Recall/safety events — linked via `device_id` |
| manufacturers.csv | 32,531 | Manufacturer info — linked via `manufacturer_id` |

---

## Key Data Findings

- `risk_class` is missing in 72% of rows
- Clean labels (1, 2, 3) exist only for USA records → ~32,600 usable labeled rows
- Class imbalance: Class II ≈ 76%, Class I ≈ 17%, Class III ≈ 7%
- `action_classification` in events.csv is a different signal (recall severity, not device risk)

---

## Pipeline Steps

### 1. Data Cleaning
- Filter `risk_class` to clean values: 1, 2, 3 only
- Normalize `action_classification` inconsistent formats (Class 2 / II / 2 → 2)
- Handle missing values per column strategy

### 2. Data Integration
- Join devices ← events (aggregate, not row-duplicate)
- Join devices ← manufacturers

### 3. Feature Engineering

| Feature Group | Features |
|--------------|---------|
| Device | classification, description length, implanted flag |
| Text (NLP) | TF-IDF on description (top N terms) |
| Manufacturer | total recall count, distinct countries, repeat-offender flag |
| Event History | total_events, recall_count, distinct_event_types |

> **Data leakage note:** Use manufacturer-level aggregates across *other* devices, not the device's own event count, to avoid leakage.

### 4. Train / Test Split
- 80% train / 20% test
- Stratified split to preserve class proportions across all three classes

### 5. Models Trained

| Model | Role |
|-------|------|
| Logistic Regression | Simple baseline |
| Random Forest | Non-linear baseline |
| XGBoost | Primary candidate |

- Class imbalance handled via `class_weight='balanced'` (LR, RF) and `compute_sample_weight('balanced')` (XGBoost)

### 6. Evaluation Metrics

- **Primary:** Macro-F1 (handles class imbalance)
- **Also reported:** Per-class Precision, Recall, F1, Confusion Matrix

### 7. Export

```python
import joblib
joblib.dump(preprocessor, "outputs/preprocessor.pkl")          # preprocessing.ipynb
shutil.copy("outputs/preprocessor.pkl", "../backend/app/ml/pipeline.pkl")
joblib.dump(best_model, "../backend/app/ml/model.pkl")           # model_training.ipynb
```

**Note**: `pipeline.pkl` is the fitted preprocessor (TF-IDF + OHE + scaler). It is fit **only on X_train** in `preprocessing.ipynb` and never refit at inference time.

---

## Inference Flow

```
User Input (description + classification + manufacturer)
    ↓
pipeline.pkl  →  transform features
    ↓
model.pkl  →  predict_proba
    ↓
{ predicted_class, confidence, probabilities }
```

---

## Model Versioning

Each trained model is recorded in the `model_versions` DB table with Macro-F1, precision, recall, and an `is_active` flag.
