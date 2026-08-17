# ML Pipeline — Medical Device Failure Prediction

## Overview

This document describes the end-to-end machine learning pipeline for predicting whether a medical device is likely to fail, based on historical recall, safety alert, and field safety notice data from the ICIJ Implant Files dataset.

The pipeline is split across two Jupyter notebooks:

| Notebook | Purpose | Outputs |
|---|---|---|
| `notebook/new_preprocessing_eda.ipynb` | EDA, label construction, feature engineering, preprocessing | `outputs/train.csv`, `outputs/test.csv`, `outputs/preprocessor.pkl`, `outputs/eda_summary.json` |
| `notebook/model_training.ipynb` | Model selection, threshold tuning, evaluation, export | `backend/app/ml/model.pkl`, `backend/app/ml/pipeline.pkl`, `outputs/metrics.json` |

**Run order:** preprocessing notebook first, then model training.

---

## 1. Problem Framing

### Target Variable

The target is `failure` — a **binary label** (0 = no failure, 1 = failure) derived from a risk score built on each device's historical recall events.

**Why binary, not multi-class?** The mentor's guidance was: *"failure yes/no should be there; classification is additional info; arriving at yes/no depends on a risk score."* The risk score is computed from two fields that carry genuine severity signal (`action_classification` and `determined_cause`), then thresholded.

### Risk Score Formula

```
risk_score = severity(action_classification)   [Class I = 3, Class II = 2, Class III = 1]
           + cause_bonus(determined_cause)      [genuine technical/design/material cause = +1, administrative = −1]

failure = 1  if max(risk_score) across a device's events >= 3   else 0
```

The device-level score is the **maximum** event-level score — i.e., the most severe event on record for that device.

### Why USA-Only?

The dataset is global, but `action_classification` and `determined_cause` — the two fields needed to build a meaningful risk score — are populated almost exclusively for USA devices. For every other country, a single `type` value accounts for ~100% of that country's events (e.g., Germany/Switzerland/Ireland always "Field Safety Notice", Spain always "Recall / Safety Alert"). A model trained on that signal would simply learn which country filed the paperwork, not actual device risk.

**USA subset size:** 33,662 devices, 35,826 events.

---

## 2. Label Distribution

| Label | Count | Proportion |
|---|---|---|
| 0 (No failure) | 18,301 | 54.4% |
| 1 (Failure) | 15,361 | 45.6% |

The classes are near-balanced (54/46 split), so no class-weighting or oversampling is required.

---

## 3. Feature Engineering

### Leakage Discipline

`action_classification` and `determined_cause` are used **only** to build the label. They are explicitly excluded from model input features, because a real "new" device being scored for the first time would not have them yet.

### Features Used

| Feature | Type | Description |
|---|---|---|
| `classification` | Categorical | FDA device classification category (e.g., "General Hospital and Personal Use Devices") |
| `description` | Text | Free-text device description |
| `mfr_loo_event_count` | Numeric | Manufacturer's total event count, **excluding** the target device's own events (leave-one-out) |
| `mfr_countries_all` | Numeric | Number of distinct countries in which the manufacturer has events |
| `mfr_devices_all` | Numeric | Number of distinct devices the manufacturer has on record |
| `description_len` | Numeric | Character length of the device description |
| `classification_prior_count` | Numeric | Total USA events in this FDA classification across all devices (point-in-time safe cumulative count) |
| `event_year` | Numeric | Year of the device's first event — controls for the reporting-era confound |

### Leave-One-Out Manufacturer Aggregates

Manufacturer-level aggregates use `determined_cause`/`action_classification` from **other devices only** — each device's own events are explicitly excluded from its own manufacturer's aggregate. This is a leave-one-out encoding that removes any doubt about data leakage.

### Classification Prior Count

`classification_prior_count` is a cumulative count of past USA events in the same FDA classification, computed **point-in-time safely**: for each device, only events that occurred before that device's first event are counted. This prevents future leakage.

**Signal strength:** The observed failure rate increases monotonically with `classification_prior_count` — from 0% for classifications with no prior events to 30.5% for the most active classifications. This is a real signal, not noise.

**Confound with calendar year:** Classifications with more prior events also tend to be older (more time to accumulate events). `event_year` is included alongside `classification_prior_count` to let the model separate the two effects.

### Event Year

`event_year` is the year of the device's first event. It controls for the reporting-era confound: the ICIJ dataset shows a sharp increase in failure rates between 2005–2009 as the FDA reporting system matured, not because devices became more dangerous. Without `event_year`, the model would partially learn "older devices = higher risk" rather than genuine device risk.

At inference time, `event_year` is always set to the current calendar year — a new device being submitted today is being evaluated in the current reporting era.

---

## 4. Escalation Rule (Post-Model)

`known_prior_incidents` is **not** a model feature. It is applied as a transparent post-model business rule:

```
if known_prior_incidents >= 2 AND prob_failure >= 0.30:
    escalated = True
    if predicted_label == "No Failure": override to "Failure"
```

**Why not a model feature?** Per-device incident history showed no learnable pattern in training data — only 1.7% of devices have more than one event, and severity stays flat across that group. Including it as a feature would add noise without signal. Applying it as an explicit rule is more transparent and auditable.

**Why both conditions must be met?** The probability threshold (0.30) ensures the escalation only fires when the model already sees some elevated risk. A device with 3 prior incidents but P(failure) = 0.05 is likely a data entry error or a genuinely low-risk device — escalating it would generate false alarms.

---

## 5. Preprocessing Pipeline

Built with scikit-learn `ColumnTransformer`:

| Branch | Features | Transformer |
|---|---|---|
| Numeric | `mfr_loo_event_count`, `mfr_countries_all`, `mfr_devices_all`, `description_len`, `classification_prior_count`, `event_year` | `StandardScaler` |
| Categorical | `classification` | `OneHotEncoder(handle_unknown='ignore')` |
| Text | `description` | `TfidfVectorizer(max_features=800, stop_words='english', ngram_range=(1,2))` |

**Transformed feature dimensionality:** 821 features (6 numeric + ~15 OHE + 800 TF-IDF).

The fitted preprocessor is saved to `outputs/preprocessor.pkl` and later copied to `backend/app/ml/pipeline.pkl` for serving.

---

## 6. Train / Test Split

- **Split ratio:** 80% train / 20% test
- **Stratified** on `failure` to preserve class balance
- **Random seed:** 42

| Split | Rows | Failure Rate |
|---|---|---|
| Train | 26,929 | 45.6% |
| Test | 6,733 | 45.6% |

---

## 7. Model Selection

Three candidate models were evaluated via **5-fold stratified cross-validation** on the training set, scored by ROC-AUC:

| Model | CV ROC-AUC | Std Dev |
|---|---|---|
| Logistic Regression | 0.7936 | ±0.0055 |
| Random Forest | 0.8419 | ±0.0083 |
| **XGBoost** | **0.8551** | **±0.0070** |

**Selected model: XGBoost** (highest mean CV ROC-AUC).

XGBoost hyperparameters:
```python
XGBClassifier(
    n_estimators=150,
    learning_rate=0.08,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric='logloss',
    random_state=42,
    n_jobs=-1
)
```

---

## 8. Decision Threshold Tuning

Rather than assuming a threshold of 0.5, the optimal threshold is found by searching over out-of-fold (OOF) predictions from the training set — the test set is never touched during this step.

**Search range:** 0.30 to 0.71 in steps of 0.02
**Objective:** maximize F1 score on OOF predictions

| Threshold | OOF F1 |
|---|---|
| 0.50 (default) | 0.7311 |
| **0.42 (selected)** | **0.7594** |

The tuned threshold (0.42) is wrapped into a `ThresholdedClassifier` from `notebook/model_classes.py`, which overrides `predict()` to apply the custom threshold while `predict_proba()` still returns raw probabilities.

---

## 9. Final Model Evaluation (Test Set)

The test set is touched **exactly once** — after all training and tuning decisions are finalized.

### Classification Report — Default Threshold (0.50)

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| No failure | 0.77 | 0.82 | 0.79 | 3,661 |
| Failure | 0.77 | 0.70 | 0.73 | 3,072 |
| **Macro avg** | **0.77** | **0.76** | **0.76** | **6,733** |

### Classification Report — Tuned Threshold (0.42)

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| No failure | 0.83 | 0.69 | 0.76 | 3,661 |
| Failure | 0.70 | 0.83 | 0.76 | 3,072 |
| **Macro avg** | **0.76** | **0.76** | **0.76** | **6,733** |

### Summary Metrics

| Metric | Value |
|---|---|
| Test ROC-AUC | **0.8572** |
| Test F1 (default threshold 0.50) | 0.7319 |
| Test F1 (tuned threshold 0.42) | **0.7581** |

The tuned threshold improves recall for the "Failure" class (0.70 → 0.83) at the cost of some precision (0.77 → 0.70), which is the right trade-off for a safety-critical application where missing a true failure is more costly than a false alarm.

---

## 10. Model Artifacts

| File | Description |
|---|---|
| `backend/app/ml/model.pkl` | `ThresholdedClassifier` wrapping the fitted XGBoost model with threshold=0.42 |
| `backend/app/ml/pipeline.pkl` | Fitted `ColumnTransformer` preprocessor (TF-IDF + OHE + Scaler) |
| `notebook/model_classes.py` | Source definitions for `ThresholdedClassifier` |
| `outputs/metrics.json` | Final test metrics (ROC-AUC, F1, threshold) |
| `outputs/eda_summary.json` | Dataset statistics, feature list, leakage notes |

---

## 11. Inference Flow

At prediction time (FastAPI `/api/v1/predict`):

1. Receive JSON payload with `description`, `classification`, `manufacturer_name` (optional), `device_name` (optional), `known_prior_incidents` (optional).
2. Look up `mfr_loo_event_count`, `mfr_countries_all`, `mfr_devices_all` from `manufacturer_features` table via fuzzy name match. Use safe defaults if not found.
3. Look up `classification_prior_count` from `classification_features` table by exact classification match. Set `event_year` to current year. Use safe defaults if not found.
4. Compute `description_len`. Build a single-row DataFrame with all 8 features.
5. `pipeline.pkl` → `transform()` → 821-dimensional sparse feature vector.
6. `model.pkl` → `predict_proba()` → `[P(no_failure), P(failure)]`; `predict()` → 0 or 1 (applies threshold=0.42 internally).
7. Apply escalation rule: if `known_prior_incidents >= 2` AND `prob_failure >= 0.30`, set `escalated=True` and override label to Failure if needed.
8. Return full prediction response including `escalated` and `escalation_note`.

---

## 12. Design Decisions & Alternatives

### Why not use `action_classification` / `determined_cause` as features?

These fields are the **inputs to the label construction**, not independent signals. Including them as features would be direct data leakage — the model would trivially learn to predict the label from the very fields used to define it.

### Why leave-one-out for manufacturer aggregates?

A simpler approach (aggregate all events per manufacturer, then join) would allow a device's own events to influence its own manufacturer aggregate, creating a subtle leakage path. Leave-one-out closes this gap.

### Why tune the threshold on OOF predictions rather than the test set?

Tuning on the test set would constitute test set contamination — the reported test metrics would be optimistically biased. OOF predictions are generated entirely from the training set, so the test set remains a clean held-out evaluation.

### Why XGBoost over Logistic Regression or Random Forest?

XGBoost achieved the highest CV ROC-AUC (0.8551 vs 0.8419 for RF and 0.7936 for LR). It also handles sparse TF-IDF features efficiently and is robust to the mixed feature types (numeric + categorical + text) in this dataset.

### Why is `known_prior_incidents` a post-model rule rather than a model feature?

Per-device incident history showed no learnable pattern in training data — only 1.7% of devices have more than one event, and severity stays flat across that group. A model feature with near-zero variance and no signal would add noise. Applying it as an explicit, auditable business rule is more transparent and easier to adjust without retraining.

### Why include both `classification_prior_count` and `event_year`?

`classification_prior_count` is partially confounded with calendar year — classifications with more prior events also tend to be older. Including `event_year` alongside it lets the model disentangle the two effects: "this classification has many prior events" vs "this device was filed in a later year when reporting rates were higher."
