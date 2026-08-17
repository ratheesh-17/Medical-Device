# API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/docs` (Swagger UI)

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness + readiness check |
| POST | `/predict` | Predict failure risk for a device |
| GET | `/predictions` | Paginated prediction history |
| GET | `/metrics` | Active model performance metrics |
| GET | `/metrics/all` | All model versions |
| GET | `/manufacturers` | Manufacturer list for autocomplete dropdown |

---

## POST `/predict`

Accepts device information, looks up manufacturer and classification history from the database, runs the ML model, applies the escalation rule, persists the result, and returns the prediction.

### Request Body

```json
{
  "description": "Implantable cardiac pacemaker for rhythm management",
  "classification": "Cardiovascular Devices",
  "manufacturer_name": "Medtronic",
  "device_name": "Evera MRI ICD",
  "known_prior_incidents": 0
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `description` | string (min 5 chars) | Yes | Free-text device description — primary ML signal |
| `classification` | string | Yes | FDA device category (e.g. `"Cardiovascular Devices"`) |
| `manufacturer_name` | string | No | Used to look up manufacturer history features from DB |
| `device_name` | string | No | Product name — display only, not used by model |
| `known_prior_incidents` | int | No | Number of known prior incidents for this specific device — used by the post-model escalation rule only, not a model feature |

**How manufacturer features are resolved:**
- If `manufacturer_name` is provided, the backend does a case-insensitive fuzzy match (`ILIKE %name%`) against the `manufacturers` table and retrieves the precomputed `manufacturer_features` row.
- If no match is found, or `manufacturer_name` is omitted, safe defaults are used: `mfr_loo_event_count=0`, `mfr_countries_all=1`, `mfr_devices_all=0`.

**How classification features are resolved:**
- The backend looks up `classification_prior_count` from the `classification_features` table by exact match on `classification`.
- `event_year` is always set to the current calendar year for new submissions — it controls for the reporting-era confound, not the device's age.
- If no match is found, safe defaults are used: `classification_prior_count=0`, `event_year=current_year`.

### Response

```json
{
  "predicted_failure": true,
  "predicted_label": "Failure",
  "confidence": 0.7812,
  "low_confidence_flag": false,
  "prob_failure": 0.7812,
  "prob_no_failure": 0.2188,
  "top_features": [
    {"feature": "tfidf__cardiac", "importance": 0.0341},
    {"feature": "tfidf__pacemaker", "importance": 0.0289},
    {"feature": "mfr_loo_event_count", "importance": 0.0201}
  ],
  "escalated": false,
  "escalation_note": null,
  "model_version": "1.0.0"
}
```

| Field | Type | Description |
|---|---|---|
| `predicted_failure` | bool | `true` = Failure, `false` = No Failure |
| `predicted_label` | string | `"Failure"` or `"No Failure"` |
| `confidence` | float | Probability of the predicted class (0–1) |
| `low_confidence_flag` | bool | `true` if confidence < 0.60 — signals uncertain prediction |
| `prob_failure` | float | Raw P(failure) from model |
| `prob_no_failure` | float | Raw P(no failure) from model |
| `top_features` | array | Up to 5 most influential features for this prediction |
| `escalated` | bool | `true` if the post-model escalation rule was triggered |
| `escalation_note` | string \| null | Human-readable explanation when `escalated=true` |
| `model_version` | string | API version at time of prediction |

**Decision threshold:** The model applies a tuned threshold of **0.42** (not the default 0.50). A device is predicted as Failure if `P(failure) >= 0.42`. This threshold was tuned on out-of-fold training predictions to maximise F1, and improves Failure recall from 0.70 → 0.83.

**Escalation rule (post-model):** If `known_prior_incidents >= 2` AND `prob_failure >= 0.30`, the prediction is escalated: `escalated` is set to `true`, and if the model predicted No Failure, the label is overridden to Failure. This is a transparent business rule applied after the model — it is not a learned model weight. Per-device incident history showed no learnable pattern in training data (only 1.7% of devices have >1 event, severity stays flat), so it is applied as an explicit rule rather than a feature.

**Error responses:**

| Status | Condition |
|---|---|
| 503 | Model files not loaded (run notebooks first) |
| 500 | Unexpected inference error |

---

## GET `/predictions`

Returns paginated prediction history, newest first.

### Query Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `skip` | int (≥0) | 0 | Number of records to skip |
| `limit` | int (1–200) | 50 | Max records to return |

### Response

Array of prediction records:

```json
[
  {
    "id": 42,
    "input_device_name": "Evera MRI ICD",
    "input_description": "Implantable cardiac pacemaker...",
    "input_classification": "Cardiovascular Devices",
    "input_manufacturer": "Medtronic",
    "input_known_prior_incidents": 0,
    "predicted_failure": true,
    "predicted_label": "Failure",
    "prob_failure": 0.7812,
    "prob_no_failure": 0.2188,
    "confidence": 0.7812,
    "low_confidence_flag": false,
    "escalated": false,
    "escalation_note": null,
    "model_version": "1.0.0",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

---

## GET `/metrics`

Returns the currently active model's performance metrics.

### Response

```json
{
  "roc_auc": 0.8553,
  "f1_tuned": 0.7528,
  "f1_default": 0.7308,
  "threshold": 0.42
}
```

| Field | Description |
|---|---|
| `roc_auc` | Test ROC-AUC (threshold-independent) |
| `f1_tuned` | Test F1 at tuned threshold (0.42) |
| `f1_default` | Test F1 at default threshold (0.50) — baseline comparison |
| `threshold` | Decision threshold applied by the model |

**Error:** 404 if no active model is found in `model_versions` table (run `seed_db.py`).

---

## GET `/metrics/all`

Returns all model versions ordered by training date (newest first). Same schema as `/metrics` but returns an array.

---

## GET `/manufacturers`

Returns manufacturer names for the React autocomplete dropdown.

### Query Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `q` | string | `""` | Search query — filters by name (case-insensitive) |
| `limit` | int (1–200) | 50 | Max results |

### Response

```json
[
  {"id": 5178, "name": "Medtronic"},
  {"id": 8821, "name": "Medtronic Puerto Rico Operations Co."}
]
```

---

## GET `/health`

Liveness and readiness check. Returns overall status plus individual component statuses.

### Response

```json
{
  "status": "ok",
  "service": "MedDevice Risk Predictor API",
  "db": "ok",
  "model": "loaded",
  "pipeline": "loaded"
}
```

| `status` value | Meaning |
|---|---|
| `"ok"` | DB connected and model loaded |
| `"degraded"` | DB error or model not loaded |

---

## Inference Flow (Internal)

```
POST /predict
     │
     ▼
get_manufacturer_features(db, manufacturer_name)
     │  fuzzy ILIKE lookup → manufacturer_features table
     │  returns: mfr_loo_event_count, mfr_countries_all, mfr_devices_all
     ▼
get_classification_features(db, classification)
     │  exact match → classification_features table
     │  returns: classification_prior_count, event_year (always current year)
     ▼
prediction_service.predict(description, classification, known_prior_incidents, **mfr_features, **clf_features)
     │  builds DataFrame row with 8 features
     │  pipeline.transform() → 821-dim sparse vector
     │  model.predict_proba() → [P(no_failure), P(failure)]
     │  model.predict()       → 0|1 (applies threshold=0.42)
     │
     │  POST-MODEL ESCALATION RULE:
     │  if known_prior_incidents >= 2 AND prob_failure >= 0.30:
     │      escalated = True
     │      if predicted_label == "No Failure": override to "Failure"
     ▼
save_prediction(db, request, response)
     │  writes to predictions table (incl. escalated, escalation_note)
     ▼
PredictResponse → JSON
```
