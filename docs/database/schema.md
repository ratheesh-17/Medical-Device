# Database Schema

MySQL database: `meddevice`

---

## Tables Overview

| Table | Purpose | Populated by |
|---|---|---|
| `manufacturers` | One row per manufacturer from ICIJ dataset | `seed_db.py` |
| `manufacturer_features` | Precomputed LOO event aggregates per manufacturer | `seed_db.py` |
| `classification_features` | Precomputed event aggregates per FDA classification | `seed_db.py` |
| `devices` | USA device records from ICIJ dataset | `seed_db.py` |
| `predictions` | Every inference request + result | FastAPI at runtime |
| `model_versions` | Trained model metadata and metrics | `seed_db.py` |
| `device_risk_scores` | Pre-computed risk scores (batch_predict.py) | `batch_predict.py` (optional) |
| `users` | App user accounts (technician + manufacturer roles) | `seed_users.py` |
| `alerts` | High-risk prediction alerts routed to manufacturers | FastAPI at runtime |

---

## Table Definitions

### `manufacturers`

Sourced from `manufacturers-1681209657.csv`. All 31,827 manufacturers are seeded regardless of country.

| Column | Type | Notes |
|---|---|---|
| `id` | INT PK | Original ICIJ manufacturer ID |
| `name` | VARCHAR(500) | Manufacturer name — used for fuzzy lookup at inference |

> The manufacturers CSV has no `country` column. Country information lives on the `devices` and `events` rows.

---

### `manufacturer_features`

Precomputed manufacturer-level event aggregates. Populated once by `seed_db.py` using the same LOO logic as `new_preprocessing_eda.ipynb`. FastAPI reads these at prediction time — never recomputes per-request.

**Why precompute?** The manufacturer aggregates require joining events → devices → manufacturers across ~35k rows. Doing this per inference request would be slow and would risk diverging from the training-time computation (training-serving skew).

| Column | Type | Notes |
|---|---|---|
| `manufacturer_id` | INT PK FK → `manufacturers.id` | |
| `mfr_loo_event_count` | FLOAT | Total events for this manufacturer (leave-one-out proxy at inference) |
| `mfr_countries_all` | FLOAT | Distinct countries in manufacturer's events. Always 1.0 for USA-only data |
| `mfr_devices_all` | FLOAT | Distinct devices recalled by this manufacturer |

**LOO note:** During training, each device's own events are excluded from its manufacturer's aggregate (leave-one-out). At inference time, the stored total is used as a proxy — the LOO adjustment is negligible for manufacturers with many events, and new devices have no events to exclude anyway.

**mfr_countries_all is always 1.0** for this dataset. The USA-only filter means every event in the training set is from the USA, so `nunique(country) = 1` for every manufacturer. The column is kept for schema completeness and future extensibility.

---

### `classification_features`

Precomputed classification-level event aggregates. 17 rows total (one per FDA device classification). Populated once by `seed_db.py`.

| Column | Type | Notes |
|---|---|---|
| `classification` | VARCHAR(255) PK | FDA device classification category |
| `classification_prior_count` | FLOAT | Total USA events in this classification across all devices |
| `event_year` | FLOAT | Median event year for this classification (stored but not used at inference — current year is always used instead) |

**Why `classification_prior_count`?** This feature captures how "active" a classification category is in the recall/safety-alert system. Classifications with more historical events have a higher observed failure rate (0% → 30.5% trend across the range).

**Why always use current year for `event_year` at inference?** A new device being submitted today is being evaluated in the current reporting era, not the historical median.

---

### `devices`

Sourced from `devices-1681209661.csv`. USA-only subset (33,657 rows). Stores device metadata for lookup at prediction time.

| Column | Type | Notes |
|---|---|---|
| `id` | INT PK | Original ICIJ device ID |
| `name` | VARCHAR(1000) | Device product name (1000 chars to accommodate long names) |
| `classification` | VARCHAR(255) | FDA device category |
| `description` | TEXT | Free-text device description — primary ML signal |
| `manufacturer_id` | INT FK → `manufacturers.id` | |
| `country` | VARCHAR(100) | Country of the device record |

---

### `predictions`

Every inference request and its result. Written by FastAPI on every `POST /api/v1/predict` call. Powers the history dashboard.

| Column | Type | Notes |
|---|---|---|
| `id` | INT PK AUTO | |
| `device_id` | INT FK → `devices.id` NULLABLE | Links prediction to the looked-up device |
| `input_device_name` | VARCHAR(500) NULLABLE | Device name from DB at time of prediction |
| `input_description` | TEXT | Device description used for inference |
| `input_classification` | VARCHAR(255) | FDA category used for inference |
| `input_manufacturer` | VARCHAR(500) NULLABLE | Manufacturer name used for inference |
| `input_known_prior_incidents` | INT NULLABLE | Technician-reported prior incidents |
| `predicted_failure` | BOOLEAN | `TRUE` = Failure, `FALSE` = No Failure |
| `predicted_label` | VARCHAR(20) | `"Failure"` or `"No Failure"` |
| `prob_failure` | FLOAT | P(failure) from model |
| `prob_no_failure` | FLOAT | P(no failure) from model |
| `confidence` | FLOAT | P(predicted class) |
| `low_confidence_flag` | BOOLEAN | `TRUE` if confidence < 0.60 |
| `escalated` | BOOLEAN | `TRUE` if post-model escalation rule was triggered |
| `escalation_note` | VARCHAR(500) NULLABLE | Human-readable explanation when escalated |
| `model_version` | VARCHAR(100) | `APP_VERSION` from config at time of prediction |
| `created_at` | DATETIME | Server-side timestamp (MySQL `NOW()`) |

---

### `model_versions`

One row per trained model. Seeded from `notebook/outputs/metrics.json` by `seed_db.py`. The active model (`is_active = TRUE`) is what `/api/v1/metrics` returns.

| Column | Type | Notes |
|---|---|---|
| `id` | INT PK AUTO | |
| `version_name` | VARCHAR(100) UNIQUE | e.g. `"xgboost_binary_v2"` |
| `algorithm` | VARCHAR(100) | e.g. `"XGBoost + ThresholdedClassifier"` |
| `roc_auc` | FLOAT | Test ROC-AUC (0.8553) |
| `f1_tuned` | FLOAT | Test F1 at tuned threshold (0.7528) |
| `f1_default` | FLOAT | Test F1 at default threshold 0.50 (0.7308) |
| `threshold` | FLOAT | Tuned decision threshold (0.42) |
| `is_active` | BOOLEAN | Only one row should be TRUE at a time |
| `trained_at` | DATETIME | Server-side timestamp |

---

### `device_risk_scores`

Optional pre-computed risk scores for all USA devices, populated by `scripts/batch_predict.py`. Not used in the current prediction flow (predictions are computed on-demand per device ID lookup).

| Column | Type | Notes |
|---|---|---|
| `device_id` | INT PK FK → `devices.id` | |
| `prob_failure` | FLOAT | Pre-computed P(failure) |
| `predicted_failure` | BOOLEAN | Pre-computed label at threshold 0.42 |
| `computed_at` | DATETIME | Timestamp of batch computation |

---

### `users`

App user accounts. Populated by `seed_users.py`. Two roles: `user` (technician) and `manufacturer`.

| Column | Type | Notes |
|---|---|---|
| `id` | INT PK AUTO | |
| `username` | VARCHAR(100) UNIQUE | `"user"` for technician; `"mfr_<id>"` for manufacturers |
| `hashed_password` | VARCHAR(255) | bcrypt hash |
| `role` | VARCHAR(20) | `"user"` or `"manufacturer"` |
| `manufacturer_id` | INT FK → `manufacturers.id` NULLABLE | NULL for technician accounts |
| `created_at` | DATETIME | Server-side timestamp |

**Seeded accounts:**
- 1 technician: `user` / `user123`
- 3,952 manufacturer accounts: `mfr_<manufacturer_id>` / `mfr123` — one for every manufacturer with at least one USA device

**Password hashing:** Both passwords are hashed exactly once each, then the hash string is reused for all bulk inserts. This avoids 3,952 bcrypt operations and completes in seconds.

**bcrypt version:** Must use `bcrypt==4.0.1`. Newer versions break passlib's `CryptContext`.

---

### `alerts`

High-risk prediction alerts. Created automatically by `POST /predict` when `prob_failure >= 0.42` AND the device's manufacturer has a registered `User` account. Displayed in the manufacturer dashboard.

| Column | Type | Notes |
|---|---|---|
| `id` | INT PK AUTO | |
| `device_id` | INT FK → `devices.id` | The device that triggered the alert |
| `manufacturer_id` | INT FK → `manufacturers.id` | Routes the alert to the correct manufacturer |
| `prob_failure` | FLOAT | P(failure) that triggered the alert |
| `predicted_label` | VARCHAR(20) | `"Failure"` or `"No Failure"` |
| `triggered_by` | VARCHAR(100) | Username of the technician who ran the prediction |
| `status` | VARCHAR(20) | `"unread"` or `"read"` |
| `created_at` | DATETIME | Server-side timestamp |

**Alert routing rule:** An alert is only created if `db.query(User).filter(User.manufacturer_id == device.manufacturer_id, User.role == 'manufacturer').first()` returns a result. This prevents orphan alerts for manufacturers with no registered account.

---

## Entity Relationships

```
manufacturers        (1) ──── (1) manufacturer_features
manufacturers        (1) ──── (N) devices
manufacturers        (1) ──── (1) users  [manufacturer accounts]
manufacturers        (1) ──── (N) alerts
devices              (1) ──── (N) predictions
devices              (1) ──── (1) device_risk_scores  [optional]
devices              (1) ──── (N) alerts
classification_features — standalone lookup table (keyed by classification string)
users — standalone auth table (manufacturer_id FK links to manufacturers)
```

---

## Seeding Order

Run in this order after setting up MySQL:

```bash
cd backend
python -m scripts.seed_db      # tables + manufacturers + devices + features + model_versions
python -m scripts.seed_users   # user accounts (depends on manufacturers being seeded first)
```

**Delete order in seed_db.py** (respects FK constraints):
1. `Prediction` (FK → devices)
2. `Device` (FK → manufacturers)
3. `ManufacturerFeatures` (FK → manufacturers)
4. `Manufacturer`

**seed_users.py** deletes all `User` rows and re-inserts. It does not touch any other table.

---

## Re-seeding

Re-running `seed_db.py` is safe — it deletes and re-inserts all seeded data. After re-running `seed_db.py`, you must also re-run `seed_users.py` only if you ran `reset_db.py` (which drops all tables including `users`). `seed_db.py` alone does not touch the `users` table.
