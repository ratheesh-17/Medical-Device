# Database Schema

MySQL database: `meddevice`

---

## Tables Overview

| Table | Purpose | Populated by |
|---|---|---|
| `manufacturers` | One row per manufacturer from ICIJ dataset | `seed_db.py` |
| `manufacturer_features` | Precomputed LOO event aggregates per manufacturer | `seed_db.py` |
| `classification_features` | Precomputed event aggregates per FDA classification | `seed_db.py` |
| `devices` | Device records from ICIJ dataset | `seed_db.py` (future) |
| `predictions` | Every inference request + result | FastAPI at runtime |
| `model_versions` | Trained model metadata and metrics | `seed_db.py` |

---

## Table Definitions

### `manufacturers`

Sourced from `manufacturers-1681209657.csv`. All 31,827 manufacturers are seeded regardless of country — the USA-only filter applies to `manufacturer_features`, not here.

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
| `mfr_countries_all` | FLOAT | Distinct countries in manufacturer's events. Constant = 1.0 for USA-only data |
| `mfr_devices_all` | FLOAT | Distinct devices recalled by this manufacturer |

**LOO note:** During training, each device's own events are excluded from its manufacturer's aggregate (leave-one-out). At inference time, the stored total is used as a proxy — the LOO adjustment is negligible for manufacturers with many events, and new devices have no events to exclude anyway.

**mfr_countries_all is always 1.0** for this dataset. The USA-only filter means every event in the training set is from the USA, so `nunique(country) = 1` for every manufacturer. The column is kept for schema completeness and future extensibility.

---

### `classification_features`

Precomputed classification-level event aggregates. One row per FDA device classification (17 rows total). Populated once by `seed_db.py`. FastAPI reads these at prediction time alongside manufacturer features.

| Column | Type | Notes |
|---|---|---|
| `id` | INT PK AUTO | |
| `classification` | VARCHAR(255) UNIQUE | FDA device classification category |
| `classification_prior_count` | FLOAT | Total USA events in this classification across all devices |
| `event_year` | FLOAT | Median event year for this classification (stored but not used at inference — current year is always used instead) |

**Why `classification_prior_count`?** This feature captures how "active" a classification category is in the recall/safety-alert system. Classifications with more historical events have a higher observed failure rate (0% → 30.5% trend across the range). It is partially confounded with calendar year (more events were filed in later years as the reporting system matured), which is why `event_year` is included alongside it.

**Why always use current year for `event_year` at inference?** A new device being submitted today is being evaluated in the current reporting era, not the historical median. Using the current year lets the model correctly interpret `classification_prior_count` in its temporal context.

---

### `devices`

Sourced from `devices-1681209661.csv`. Stores device metadata for reference and for linking predictions to source records.

| Column | Type | Notes |
|---|---|---|
| `id` | INT PK | Original ICIJ device ID |
| `name` | VARCHAR(500) | Device product name |
| `classification` | VARCHAR(255) | FDA device category |
| `description` | TEXT | Free-text device description |
| `manufacturer_id` | INT FK → `manufacturers.id` | |
| `country` | VARCHAR(100) | Country of the device record |

---

### `predictions`

Every inference request and its result. Written by FastAPI on every `/api/v1/predict` call. Powers the history dashboard.

| Column | Type | Notes |
|---|---|---|
| `id` | INT PK AUTO | |
| `device_id` | INT FK → `devices.id` NULLABLE | NULL for ad-hoc predictions not linked to a known device |
| `input_device_name` | VARCHAR(500) NULLABLE | Product name entered by user (display only) |
| `input_description` | TEXT | Device description submitted |
| `input_classification` | VARCHAR(255) | FDA category submitted |
| `input_manufacturer` | VARCHAR(500) NULLABLE | Manufacturer name submitted |
| `input_known_prior_incidents` | INT NULLABLE | Known prior incidents submitted by technician |
| `predicted_failure` | BOOLEAN | `TRUE` = Failure, `FALSE` = No Failure |
| `predicted_label` | VARCHAR(20) | `"Failure"` or `"No Failure"` |
| `prob_failure` | FLOAT | P(failure) from model |
| `prob_no_failure` | FLOAT | P(no failure) from model |
| `confidence` | FLOAT | P(predicted class) — max of the two probabilities |
| `low_confidence_flag` | BOOLEAN | `TRUE` if confidence < 0.60 |
| `escalated` | BOOLEAN | `TRUE` if post-model escalation rule was triggered |
| `escalation_note` | TEXT NULLABLE | Human-readable explanation when escalated |
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

## Entity Relationships

```
manufacturers        (1) ──── (1) manufacturer_features
manufacturers        (1) ──── (N) devices
devices              (1) ──── (N) predictions
classification_features — standalone lookup table (keyed by classification string)
```

---

## Seeding

Run once after setting up MySQL and before starting the API:

```bash
cd backend
python -m scripts.seed_db
```

What it does:
1. Creates all tables via `Base.metadata.create_all()`
2. Loads all 31,827 manufacturers from CSV
3. Filters to USA-only devices/events (33,657 devices, 35,818 events)
4. Computes `manufacturer_features` aggregates (3,952 rows)
5. Computes `classification_features` aggregates (17 rows — one per FDA classification)
6. Seeds `model_versions` from `notebook/outputs/metrics.json`

Re-running is safe — it deletes and re-inserts `manufacturers`, `manufacturer_features`, `classification_features`, and `model_versions` each time.
