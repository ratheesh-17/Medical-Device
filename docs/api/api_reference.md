# API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs available at: `http://localhost:8000/docs`

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

Predict risk class for a medical device.

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
  "model_version": "1.0.0"
}
```

| Field | Description |
|-------|-------------|
| predicted_class | Predicted FDA risk class: I, II, or III |
| confidence | Probability of the predicted class |
| low_confidence_flag | True if confidence < 0.60 |
| probabilities | Per-class probabilities |
| model_version | Model version used |

**Error Responses**

| Code | Reason |
|------|--------|
| 503 | Model not yet loaded |
| 500 | Internal prediction error |

---

### GET /predictions

Paginated prediction history.

**Query Parameters**

| Param | Default | Description |
|-------|---------|-------------|
| skip | 0 | Records to skip |
| limit | 50 | Max records (1–200) |

**Response** — Array of prediction records.

---

### GET /metrics

Active model performance metrics.

**Response**
```json
{
  "version_name": "xgboost_v1",
  "algorithm": "XGBoost",
  "macro_f1": 0.82,
  "precision_score": 0.83,
  "recall_score": 0.81,
  "trained_at": "2025-01-01T00:00:00"
}
```

---

### GET /metrics/all

All model versions with metrics.
