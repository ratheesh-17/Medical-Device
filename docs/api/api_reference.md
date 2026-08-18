# API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/docs` (Swagger UI)

---

## Authentication

Most endpoints are open. Protected endpoints require a JWT Bearer token obtained from `POST /auth/login`.

```
Authorization: Bearer <token>
```

Tokens expire after 480 minutes (8 hours). The frontend stores the token in `localStorage` and attaches it automatically via an Axios interceptor.

---

## Endpoints Overview

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/login` | None | Get JWT token |
| GET | `/auth/me` | Any | Current user info |
| GET | `/auth/manufacturers` | None | Manufacturer accounts for login dropdown |
| GET | `/health` | None | Liveness + readiness check |
| POST | `/predict` | Optional | Predict failure risk by device ID |
| GET | `/predictions` | None | Paginated prediction history |
| GET | `/metrics` | None | Active model metrics |
| GET | `/metrics/all` | None | All model versions |
| GET | `/manufacturers` | None | Manufacturer autocomplete |
| GET | `/devices` | None | Device search by name or ID |
| GET | `/manufacturer/dashboard` | Manufacturer | Stats + classification breakdown |
| GET | `/manufacturer/devices` | Manufacturer | Paginated device list with search |
| GET | `/manufacturer/alerts` | Manufacturer | High-risk prediction alerts |
| PATCH | `/manufacturer/alerts/{id}/read` | Manufacturer | Mark alert as read |

---

## POST `/auth/login`

Authenticates a user and returns a JWT token.

### Request Body

```json
{
  "username": "user",
  "password": "user123"
}
```

For manufacturer accounts: `username` is `mfr_<manufacturer_id>` (e.g. `mfr_5247`), password is `mfr123`.

### Response

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "role": "user",
  "username": "user",
  "manufacturer_id": null,
  "manufacturer_name": null
}
```

For manufacturer login, `manufacturer_id` and `manufacturer_name` are populated.

**Error:** `401` if credentials are invalid.

---

## GET `/auth/me`

Returns the currently authenticated user's info. Requires any valid JWT.

### Response

```json
{
  "username": "mfr_5247",
  "role": "manufacturer",
  "manufacturer_id": 5247,
  "manufacturer_name": "Boston Scientific Corporation"
}
```

---

## GET `/auth/manufacturers`

Returns all seeded manufacturer accounts sorted alphabetically by name. Used by the login page dropdown.

### Response

```json
[
  {
    "username": "mfr_5247",
    "manufacturer_id": 5247,
    "name": "Boston Scientific Corporation"
  },
  ...
]
```

Returns up to 3,952 entries (all manufacturers with at least one USA device).

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

## POST `/predict`

Looks up a USA device by ID, retrieves manufacturer and classification features from the database, runs the XGBoost model, applies the escalation rule, persists the result, and — if `prob_failure ≥ 0.42` and the manufacturer has a registered account — creates an alert.

### Request Body

```json
{
  "device_id": 16284,
  "known_prior_incidents": 0
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `device_id` | int | Yes | USA device ID from the ICIJ dataset (33,657 valid IDs) |
| `known_prior_incidents` | int | No | Technician-reported prior incidents — used by post-model escalation rule only |

### Response

```json
{
  "device_id": 16284,
  "device_name": "ACCOLADE MRI PACEMAKER",
  "device_description": "Implantable cardiac pacemaker...",
  "device_classification": "Cardiovascular Devices",
  "manufacturer_name": "Boston Scientific Corporation",
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
| `device_id` | int | The looked-up device ID |
| `device_name` | string | Device product name from DB |
| `device_description` | string | Device description from DB |
| `device_classification` | string | FDA device category from DB |
| `manufacturer_name` | string | Manufacturer name from DB |
| `predicted_failure` | bool | `true` = Failure, `false` = No Failure |
| `predicted_label` | string | `"Failure"` or `"No Failure"` |
| `confidence` | float | Probability of the predicted class (0–1) |
| `low_confidence_flag` | bool | `true` if confidence < 0.60 |
| `prob_failure` | float | Raw P(failure) from model |
| `prob_no_failure` | float | Raw P(no failure) from model |
| `top_features` | array | Up to 5 most influential features for this prediction |
| `escalated` | bool | `true` if post-model escalation rule was triggered |
| `escalation_note` | string \| null | Human-readable explanation when `escalated=true` |
| `model_version` | string | API version at time of prediction |

**Decision threshold:** The model applies a tuned threshold of **0.42**. A device is predicted as Failure if `P(failure) >= 0.42`. This threshold was tuned on out-of-fold training predictions to maximise F1, improving Failure recall from 0.70 → 0.83.

**Alert creation:** If `prob_failure >= 0.42` AND the device's manufacturer has a registered `User` account with `role='manufacturer'`, an alert is created in the `alerts` table. The alert is routed to that manufacturer's dashboard. If the manufacturer has no registered account, no alert is created (prevents orphan alerts).

**Escalation rule (post-model):** If `known_prior_incidents >= 2` AND `prob_failure >= 0.30`, the prediction is escalated: `escalated` is set to `true`, and if the model predicted No Failure, the label is overridden to Failure. This is a transparent business rule applied after the model — not a learned model weight.

**Error responses:**

| Status | Condition |
|---|---|
| 404 | Device ID not found in USA dataset |
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
    "input_device_name": "ACCOLADE MRI PACEMAKER",
    "input_description": "Implantable cardiac pacemaker...",
    "input_classification": "Cardiovascular Devices",
    "input_manufacturer": "Boston Scientific Corporation",
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
  "version_name": "xgboost_binary_v2",
  "algorithm": "XGBoost + ThresholdedClassifier",
  "roc_auc": 0.8553,
  "f1_tuned": 0.7528,
  "f1_default": 0.7308,
  "threshold": 0.42,
  "trained_at": "2024-01-15T10:00:00"
}
```

**Error:** `404` if no active model is found in `model_versions` table (run `seed_db.py`).

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
  {"id": 5247, "name": "Boston Scientific Corporation"},
  {"id": 5178, "name": "Medtronic"}
]
```

---

## GET `/devices`

Searches devices by name or ID. Used by the predict page device lookup.

### Query Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `q` | string | `""` | If numeric: exact ID match. Otherwise: name ILIKE search |
| `limit` | int (1–100) | 20 | Max results |

### Response

```json
[
  {
    "id": 16284,
    "name": "ACCOLADE MRI PACEMAKER",
    "classification": "Cardiovascular Devices",
    "country": "US"
  }
]
```

---

## GET `/manufacturer/dashboard`

Returns dashboard statistics for the authenticated manufacturer. Requires `role=manufacturer` JWT.

### Response

```json
{
  "total_devices": 142,
  "total_events": 3847,
  "countries_active": 1,
  "unread_alerts": 3,
  "classification_breakdown": [
    {"classification": "Cardiovascular Devices", "count": 98},
    {"classification": "General Hospital and Personal Use Devices", "count": 44}
  ]
}
```

| Field | Source |
|---|---|
| `total_devices` | Count of devices with this `manufacturer_id` |
| `total_events` | `mfr_loo_event_count` from `manufacturer_features` |
| `countries_active` | `mfr_countries_all` from `manufacturer_features` |
| `unread_alerts` | Count of alerts with `status='unread'` for this manufacturer |
| `classification_breakdown` | Top 8 classifications by device count |

---

## GET `/manufacturer/devices`

Returns the authenticated manufacturer's devices, paginated and searchable.

### Query Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `skip` | int (≥0) | 0 | Offset |
| `limit` | int (1–200) | 50 | Max results |
| `q` | string | `""` | Filter by device name (ILIKE) |

### Response

```json
[
  {
    "id": 16284,
    "name": "ACCOLADE MRI PACEMAKER",
    "classification": "Cardiovascular Devices",
    "country": "US"
  }
]
```

---

## GET `/manufacturer/alerts`

Returns high-risk prediction alerts for the authenticated manufacturer, newest first.

### Query Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `skip` | int (≥0) | 0 | Offset |
| `limit` | int (1–200) | 50 | Max results |

### Response

```json
[
  {
    "id": 7,
    "device_id": 16284,
    "device_name": "ACCOLADE MRI PACEMAKER",
    "prob_failure": 0.7812,
    "predicted_label": "Failure",
    "triggered_by": "user",
    "status": "unread",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

---

## PATCH `/manufacturer/alerts/{id}/read`

Marks an alert as read. The alert must belong to the authenticated manufacturer.

### Response

```json
{"ok": true}
```

**Error:** `404` if alert not found or belongs to a different manufacturer.

---

## Inference Flow (Internal)

```
POST /predict  { device_id: 16284 }
     │
     ▼
db.query(Device).filter(Device.id == 16284)
     │  fetches: name, description, classification, manufacturer_id
     ▼
get_manufacturer_features(db, manufacturer_name)
     │  fuzzy ILIKE lookup → manufacturer_features table
     │  returns: mfr_loo_event_count, mfr_countries_all, mfr_devices_all
     ▼
get_classification_features(db, classification)
     │  exact match → classification_features table
     │  returns: classification_prior_count, event_year (always current year)
     ▼
prediction_service.predict(description, classification, **mfr_features, **clf_features)
     │  builds DataFrame row with 8 features
     │  pipeline.transform() → 821-dim sparse vector
     │  model.predict_proba() → [P(no_failure), P(failure)]
     │  model.predict()       → 0|1 (applies threshold=0.42 internally)
     │
     │  POST-MODEL ESCALATION RULE:
     │  if known_prior_incidents >= 2 AND prob_failure >= 0.30:
     │      escalated = True
     │      if predicted_label == "No Failure": override to "Failure"
     ▼
ALERT CREATION RULE:
     │  if prob_failure >= 0.42 AND device.manufacturer_id exists:
     │      check User table for mfr_user with role='manufacturer'
     │      if mfr_user exists: create Alert row
     │      (no alert if manufacturer has no registered account)
     ▼
save_prediction(db, request, response)
     │  writes to predictions table
     ▼
PredictResponse → JSON
```
