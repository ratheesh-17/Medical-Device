# Frontend Documentation

React application for the Medical Device Failure Risk Predictor.

Runs at `http://localhost:3000`. Communicates with the FastAPI backend at `http://localhost:8000/api/v1`.

---

## Structure

```
frontend/src/
├── components/
│   ├── Topbar.js           # Navigation bar + health status badge
│   ├── RiskBadge.js        # Failure / No Failure pill badge
│   ├── ConfidenceBar.js    # Single horizontal confidence bar
│   ├── ProbabilityBars.js  # P(Failure) + P(No Failure) bar pair
│   └── TopFeatures.js      # Feature importance list (utility component)
├── pages/
│   ├── PredictPage.js      # / — prediction form + result display
│   ├── HistoryPage.js      # /history — paginated prediction history table
│   ├── MetricsPage.js      # /metrics — model performance dashboard
│   └── HealthPage.js       # /health — backend service status
├── services/
│   └── api.js              # Axios instance + all API call functions
├── App.js                  # Router + health polling + footer
├── index.css               # All styles (single global stylesheet)
└── index.js                # React entry point
```

---

## Pages

### PredictPage — `/`

The main page. Users submit a device description and classification to get a binary failure risk prediction.

**Form fields:**

| Field | Type | Required | Sent to backend |
|---|---|---|---|
| Device Description | Textarea (min 5 chars) | Yes | `description` |
| Device Classification | Select dropdown | Yes | `classification` |
| Manufacturer | Autocomplete text input | No | `manufacturer_name` |
| Device Name | Text input | No | `device_name` |

**Stat cards (top of page):**

| Card | Source | Description |
|---|---|---|
| Predictions Run | `GET /predictions` (limit 200) | Total records in DB |
| Failure Predictions | `GET /predictions` | Count where `predicted_failure = true` |
| Low Confidence | `GET /predictions` | Count where `low_confidence_flag = true` |
| Model ROC-AUC | `GET /metrics` | `roc_auc` from active model version |

**Manufacturer autocomplete:**
- Fires `GET /manufacturers?q=<query>&limit=8` after 250 ms debounce when input length ≥ 2
- Dropdown closes on outside click (mousedown listener on document)
- Selecting a suggestion sets both the display input and `form.manufacturer_name`

**Result display (shown after successful prediction):**

```
ScoreCircle (animated ring)
  └── confidence % in teal (No Failure) or red (Failure)

predicted_label · P(failure) = XX.X%
RiskBadge

[warn-banner if low_confidence_flag]

── Failure Probability ──
ProbabilityBars (prob_failure / prob_no_failure)

── Top Influencing Features ──
factor rows: feature name + importance % with ▲/◆/▼ icon
```

**Right panel:**
- Before prediction: "How It Works" — explains Failure/No Failure labels and the 0.42 threshold decision
- After prediction: "Prediction Breakdown" — ScoreCircle, ConfidenceBar, ProbabilityBars, classification detail rows

---

### HistoryPage — `/history`

Paginated table of all past predictions, newest first.

**Columns:**

| Column | Field | Notes |
|---|---|---|
| ID | `id` | Monospace, prefixed `#` |
| Device | `input_device_name` | `—` if not provided |
| Description | `input_description` | Truncated to 190px, full text on hover |
| Classification | `input_classification` | |
| Manufacturer | `input_manufacturer` | `—` if not provided |
| Result | `predicted_failure` | RiskBadge component |
| P(Failure) | `prob_failure` | Monospace %, red if failure / teal if not |
| Confidence | `confidence` | Mini bar + % value, color-coded |
| Flag | `low_confidence_flag` | ⚠ Low (amber) or ✓ OK (teal) |
| Date | `created_at` | `en-IN` locale, medium date + short time |

**Pagination:** loads 25 records at a time. "Load More" button appends the next page. Refresh button resets to page 0.

---

### MetricsPage — `/metrics`

Model performance dashboard. Reads from `GET /metrics`.

**Stat cards:**

| Card | Field | Color |
|---|---|---|
| ROC-AUC | `roc_auc` | teal |
| F1 (Tuned 0.42) | `f1_tuned` | blue |
| F1 (Default 0.50) | `f1_default` | amber |
| Decision Threshold | `threshold` | — |

**Left panel — Metric Breakdown table:**

| Row | Value | Description |
|---|---|---|
| ROC-AUC | `roc_auc` | Threshold-independent discriminative ability |
| F1 (threshold 0.42) | `f1_tuned` | Optimised for Failure recall |
| F1 (threshold 0.50) | `f1_default` | Baseline comparison |
| Failure Recall (tuned) | 0.83 (hardcoded) | At threshold 0.42 |
| Failure Recall (default) | 0.70 (hardcoded) | At threshold 0.50 |
| Decision Threshold | `threshold` | Operating threshold |

**Right panel — Gauges:**
Three SVG ring gauges: ROC-AUC (teal), F1 Tuned (blue), F1 Default (amber).

**Right panel — Threshold Tuning Impact:**
Four bar rows comparing recall and F1 at threshold 0.50 vs 0.42, with a note explaining the safety-critical trade-off.

---

### HealthPage — `/health`

Live backend status. Calls `GET /health` on mount and on manual refresh.

**Overall banner:** green (All Systems Operational) or red (System Degraded) based on `status` field.

**Service cards:**

| Card | Key | OK value |
|---|---|---|
| MySQL Database | `db` | `"ok"` |
| ML Model | `model` | `"loaded"` |
| Preprocessor | `pipeline` | `"loaded"` |

**Raw API Response:** pretty-printed JSON of the full health response.

On error (backend unreachable), all fields are set to `"error"` and the topbar health badge turns red.

---

## Components

### Topbar

Sticky navigation bar at the top of every page.

- Brand: SentryMed logo mark (conic gradient) + name + subtitle
- Nav links: Predict Risk, History, Model Metrics, System Health — active link highlighted in teal
- Health badge (top right): polls `GET /health` once on app load via `App.js`
  - `ok` → teal dot + "All Systems OK"
  - error → red dot + "Degraded"
  - loading → grey dot + "Checking…"

---

### RiskBadge

```jsx
<RiskBadge failure={true} />   // → red pill "Failure"
<RiskBadge failure={false} />  // → teal pill "No Failure"
<RiskBadge failure={true} full />  // → "Predicted Failure"
```

Props:

| Prop | Type | Default | Description |
|---|---|---|---|
| `failure` | bool | required | `true` = Failure (red), `false` = No Failure (teal) |
| `full` | bool | `false` | Show full label text |

---

### ConfidenceBar

```jsx
<ConfidenceBar value={0.76} />
```

Single horizontal bar showing confidence percentage. Color: teal ≥ 75%, amber ≥ 50%, red < 50%.

Props:

| Prop | Type | Description |
|---|---|---|
| `value` | float (0–1) | Confidence score from prediction response |

---

### ProbabilityBars

```jsx
<ProbabilityBars probFailure={0.72} probNoFailure={0.28} />
```

Two stacked bars: Failure (red) and No Fail (teal), each showing percentage.

Props:

| Prop | Type | Description |
|---|---|---|
| `probFailure` | float (0–1) | `prob_failure` from prediction response |
| `probNoFailure` | float (0–1) | `prob_no_failure` from prediction response |

---

## API Service — `services/api.js`

All backend calls go through a single Axios instance with `baseURL: http://localhost:8000/api/v1`.

| Function | Method | Endpoint | Parameters |
|---|---|---|---|
| `predict(data)` | POST | `/predict` | `{ description, classification, manufacturer_name?, device_name? }` |
| `getManufacturers(q, limit)` | GET | `/manufacturers` | `q` (search string), `limit` (default 50) |
| `getHistory(skip, limit)` | GET | `/predictions` | `skip` (default 0), `limit` (default 50) |
| `getMetrics()` | GET | `/metrics` | — |
| `getHealth()` | GET | `/health` | — |

---

## Data Flow — Prediction

```
User fills form → handleSubmit()
        │
        ▼
predict({ description, classification, manufacturer_name, device_name })
        │  POST /api/v1/predict
        ▼
Backend:
  1. Fuzzy-match manufacturer_name → manufacturer_features (LOO aggregates)
  2. Compute description_len
  3. pipeline.transform() → 821-dim vector
  4. model.predict_proba() → [P(no_failure), P(failure)]
  5. model.predict() → 0|1 (threshold 0.42)
  6. Persist to predictions table
        │
        ▼
PredictResponse {
  predicted_failure, predicted_label,
  confidence, low_confidence_flag,
  prob_failure, prob_no_failure,
  top_features, model_version
}
        │
        ▼
setResult(res.data) → renders result panel + loadStats()
```

---

## Design Decisions

### Single global stylesheet (`index.css`)
All styles live in one file using CSS custom properties (`--teal`, `--red`, `--amber`, etc.). No CSS modules, no styled-components. This keeps the visual system consistent and easy to audit.

### Stat cards load from history + metrics, not a dedicated endpoint
`PredictPage` calls `GET /predictions?limit=200` and `GET /metrics` in parallel to populate the four stat cards. This avoids adding a `/stats` endpoint to the backend for a UI convenience feature.

### Manufacturer autocomplete is debounced at 250 ms
Prevents a DB query on every keystroke. Minimum 2 characters before firing to avoid returning all 31,827 manufacturers on a single-character input.

### Confidence color thresholds
- ≥ 75% → teal (high confidence)
- ≥ 50% → amber (moderate)
- < 50% → red (low — also triggers `low_confidence_flag` from backend at < 60%)

### `low_confidence_flag` comes from the backend
The flag is set server-side (`confidence < 0.60`) and returned in the response. The frontend does not recompute it — it only displays the warn banner when `result.low_confidence_flag === true`.

### History pagination is append-only
"Load More" appends to the existing list rather than replacing it. Refresh resets `skip` to 0 and replaces the list. This avoids a full reload on every page change while keeping the refresh button predictable.

---

## Running the Frontend

```bash
cd frontend
npm install
npm start
```

Runs at `http://localhost:3000`. Requires the backend to be running at `http://localhost:8000`.

To change the backend URL, edit the `baseURL` in `src/services/api.js`.
