# API Reference

Base URL: `http://localhost:8000/api/v1`  
Interactive docs: `http://localhost:8000/docs`

---

## Endpoints

### GET /health

Liveness check.

**Response**
```json
{ "status": "ok", "service": "MedDevice Risk Predictor API" }
```

---

### POST /predict

Predict FDA risk class for a medical device.

**Request Body**
```json
{
  "description": "Implantable cardiac pacemaker for rhythm management",
  "classification": "Cardiovascular Devices",
  "manufacturer_name": "Medtronic"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| description | string | Yes | Device description (min 5 chars) |
| classification | string | Yes | Device category |
| manufacturer_name | string | No | Manufacturer name |

**Response**
```json
{
  "predicted_class": "II",
  "confidence": 0.81,
  "low_confidence_flag": false,
  "probabilities": {
    "I": 0.12,
    "II": 0.81,
    "III": 0.07
  },
  "model_version": "1.0.0",
  "top_features": [
    { "feature": "classification_Cardiovascular Devices", "importance": 0.0842 },
    { "feature": "implantable", "importance": 0.0631 },
    { "feature": "mfr_total_events", "importance": 0.0214 }
  ]
}
```

| Field | Description |
|-------|-------------|
| predicted_class | Predicted FDA risk class: `I`, `II`, or `III` |
| confidence | True probability of the predicted class (unweighted) |
| low_confidence_flag | `true` if confidence < 0.60 |
| probabilities | Per-class true probabilities (sum to 1.0) |
| model_version | Model version used for this prediction |
| top_features | Top 5 features driving this specific prediction (feature name + weighted importance score) |

> **Note:** `confidence` and `probabilities` reflect true model probabilities. The decision rule uses per-class weights internally (I=1.8, II=1.0, III=2.2) to improve recall on minority classes, but the returned probabilities are always unweighted.

**Error Responses**

| Code | Reason |
|------|--------|
| 422 | Validation error (e.g. description too short) |
| 503 | Model not yet loaded — run notebooks first |
| 500 | Internal prediction error |

---

### GET /manufacturers

Manufacturer autocomplete for the React prediction form.

**Query Parameters**

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| q | "" | — | Search string (partial name match) |
| limit | 50 | 1–200 | Max results |

**Response**
```json
[
  { "id": 4827, "name": "Medtronic" },
  { "id": 5012, "name": "Medline Industries" }
]
```

---

### GET /predictions

Paginated prediction history.

**Query Parameters**

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| skip | 0 | ≥ 0 | Records to skip |
| limit | 50 | 1–200 | Max records to return |

**Response** — Array of prediction records:
```json
[
  {
    "id": 1,
    "input_description": "Implantable cardiac pacemaker",
    "input_classification": "Cardiovascular Devices",
    "predicted_class": "II",
    "confidence": 0.81,
    "model_version": "1.0.0",
    "created_at": "2025-01-01T12:00:00"
  }
]
```

---

### GET /metrics

Active model performance metrics.

**Response**
```json
{
  "version_name": "xgboost_v3_weighted",
  "algorithm": "XGBoost + WeightedDecisionClassifier",
  "macro_f1": 0.8014,
  "precision_score": 0.9043,
  "recall_score": 0.9336,
  "trained_at": "2025-01-01T00:00:00",
  "per_class": {
    "I":   { "precision": 0.714, "recall": 0.669, "f1": 0.691 },
    "II":  { "precision": 0.904, "recall": 0.934, "f1": 0.919 },
    "III": { "precision": 0.892, "recall": 0.716, "f1": 0.795 }
  },
  "class_weights": { "I": 1.8, "II": 1.0, "III": 2.2 }
}
```

---

### GET /metrics/all

All model versions with metrics, ordered by training date descending.

**Response** — Array of model version records (same schema as `/metrics`).

---

## Risk Class Reference

| Class | FDA Definition | Examples |
|-------|---------------|---------|
| I | Low risk — general controls sufficient | Bandages, tongue depressors |
| II | Moderate risk — special controls required | Infusion pumps, surgical gloves |
| III | High risk — premarket approval required | Pacemakers, implantable defibrillators |
