# Frontend Documentation

React application for SentryMed — Medical Device Failure Risk Predictor.

Runs at `http://localhost:3000`. Communicates with the FastAPI backend at `http://localhost:8000/api/v1`.

---

## Structure

```
frontend/src/
├── components/
│   ├── Topbar.js           # Role-aware navigation bar + health status badge + logout
│   ├── RiskBadge.js        # Failure / No Failure pill badge
│   ├── ConfidenceBar.js    # Single horizontal confidence bar
│   ├── ProbabilityBars.js  # P(Failure) + P(No Failure) bar pair
│   └── TopFeatures.js      # Feature importance list
├── context/
│   └── AuthContext.js      # Global auth state, JWT storage, login/logout
├── pages/
│   ├── LoginPage.js        # /login — tab switcher: Technician / Manufacturer
│   ├── PredictPage.js      # / — device ID lookup + prediction form + result
│   ├── HistoryPage.js      # /history — paginated prediction history table
│   ├── MetricsPage.js      # /metrics — model performance dashboard
│   ├── HealthPage.js       # /health — backend service status
│   └── mfr/
│       └── MfrDashboardPage.js  # /manufacturer — manufacturer dashboard + alerts
├── services/
│   └── api.js              # Axios instance + JWT interceptor + all API call functions
├── App.js                  # Router + role-based routing + health polling
├── index.css               # All styles (single global stylesheet)
└── index.js                # React entry point
```

---

## Auth & Routing

### AuthContext (`context/AuthContext.js`)

Global auth state provider. Wraps the entire app.

- On mount: reads JWT from `localStorage`, calls `GET /auth/me` to restore session. Sets `loading=true` until resolved.
- `login(username, password)`: calls `POST /auth/login`, stores token in `localStorage`, sets user state, returns role.
- `logout()`: clears `localStorage`, sets user to null.
- Exposes: `{ user, loading, login, logout }`

`user` shape:
```js
{
  username: "mfr_5247",
  role: "manufacturer",          // "user" | "manufacturer"
  manufacturer_id: 5247,
  manufacturer_name: "Boston Scientific Corporation"
}
```

### Role-based routing (`App.js`)

| State | Behaviour |
|---|---|
| `loading=true` | Full-screen spinner |
| `user=null` | Only `/login` accessible; all other paths redirect to `/login` |
| `user.role='manufacturer'` | Only `/manufacturer` accessible; Topbar shows manufacturer nav |
| `user.role='user'` | `/`, `/history`, `/metrics`, `/health` accessible; Topbar shows technician nav |

### JWT interceptor (`services/api.js`)

```js
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```

All API calls automatically include the token if present.

---

## Pages

### LoginPage — `/login`

Tab switcher with two modes:

**Technician tab:**
- Username field is read-only (`user`)
- Password pre-filled with `user123`
- Submit → `POST /auth/login` → navigate to `/`

**Manufacturer tab:**
- Searchable dropdown fetching from `GET /auth/manufacturers`
- On open: shows first 200 manufacturers (alphabetical)
- On type: filters all 3,952 accounts, shows up to 60 matches
- Selecting a manufacturer fills the input and sets `selected` state
- Password pre-filled with `mfr123`
- Submit → `POST /auth/login` with `mfr_<id>` username → navigate to `/manufacturer`

---

### PredictPage — `/`

The main technician page. Technicians look up a device by ID and get a failure risk prediction.

**Form fields:**

| Field | Type | Description |
|---|---|---|
| Device ID | Number input | ICIJ USA device ID (1–99999) |
| Known Prior Incidents | Number input (optional) | Used by post-model escalation rule only |

**Stat cards (top of page):**

| Card | Source |
|---|---|
| Predictions Run | `GET /predictions` (limit 200) — total count |
| Failure Predictions | Count where `predicted_failure = true` |
| Low Confidence | Count where `low_confidence_flag = true` |
| Model ROC-AUC | `GET /metrics` → `roc_auc` |

**Result display (shown after successful prediction):**

```
Device info panel:
  Device ID · Name · Classification · Manufacturer

ScoreCircle (animated ring)
  └── confidence % in teal (No Failure) or red (Failure)

predicted_label · P(failure) = XX.X%
RiskBadge

[escalation banner if escalated=true]
[warn-banner if low_confidence_flag]

── Failure Probability ──
ProbabilityBars (prob_failure / prob_no_failure)

── Top Influencing Features ──
factor rows: feature name + importance % with ▲/◆/▼ icon
```

---

### MfrDashboardPage — `/manufacturer`

Manufacturer-only page. Requires `role=manufacturer` JWT.

**Stat cards:**

| Card | Source |
|---|---|
| Total Devices | `dashboard.total_devices` |
| Total Events | `dashboard.total_events` (from manufacturer_features) |
| Countries Active | `dashboard.countries_active` |
| Unread Alerts | `dashboard.unread_alerts` |

**Classification breakdown:** Horizontal bars showing device count per FDA classification (top 8).

**Tabs:**

- **Devices tab:** Paginated table of manufacturer's devices. Search by device name. Columns: ID, Name, Classification, Country. "Load More" pagination.
- **Alerts tab:** List of high-risk prediction alerts. Each alert shows device name, failure probability, triggered-by username, timestamp, and status badge. "Mark as Read" button calls `PATCH /manufacturer/alerts/{id}/read` and updates the unread count.

**Alert system explanation panel:** Explains that alerts are created when a technician predicts `prob_failure ≥ 0.42` for one of the manufacturer's devices.

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

**Pagination:** loads 25 records at a time. "Load More" appends the next page. Refresh button resets to page 0.

---

### MetricsPage — `/metrics`

Model performance dashboard. Reads from `GET /metrics`.

**Stat cards:** ROC-AUC (teal), F1 Tuned 0.42 (blue), F1 Default 0.50 (amber), Decision Threshold.

**Left panel — Metric Breakdown table:** ROC-AUC, F1 at both thresholds, Failure Recall at both thresholds, Decision Threshold.

**Right panel — Gauges:** Three SVG ring gauges: ROC-AUC, F1 Tuned, F1 Default.

**Right panel — Threshold Tuning Impact:** Bar rows comparing recall and F1 at threshold 0.50 vs 0.42.

---

### HealthPage — `/health`

Live backend status. Calls `GET /health` on mount and on manual refresh.

**Overall banner:** green (All Systems Operational) or red (System Degraded).

**Service cards:** MySQL Database (`db`), ML Model (`model`), Preprocessor (`pipeline`).

**Raw API Response:** pretty-printed JSON of the full health response.

---

## Components

### Topbar

Sticky navigation bar. Role-aware.

- **Technician nav:** Predict Risk, History, Model Metrics, System Health
- **Manufacturer nav:** Dashboard only
- **Right side:** Health badge (polls once on app load) + username display + Logout button
- Logout calls `AuthContext.logout()` and navigates to `/login`

---

### RiskBadge

```jsx
<RiskBadge failure={true} />   // → red pill "Failure"
<RiskBadge failure={false} />  // → teal pill "No Failure"
<RiskBadge failure={true} full />  // → "Predicted Failure"
```

---

### ConfidenceBar

Single horizontal bar. Color: teal ≥ 75%, amber ≥ 50%, red < 50%.

```jsx
<ConfidenceBar value={0.76} />
```

---

### ProbabilityBars

Two stacked bars: Failure (red) and No Fail (teal).

```jsx
<ProbabilityBars probFailure={0.72} probNoFailure={0.28} />
```

---

## API Service — `services/api.js`

All backend calls go through a single Axios instance with `baseURL: http://localhost:8000/api/v1`.

| Function | Method | Endpoint | Description |
|---|---|---|---|
| `login(username, password)` | POST | `/auth/login` | Get JWT token |
| `getMe()` | GET | `/auth/me` | Current user info |
| `getMfrAccounts()` | GET | `/auth/manufacturers` | All manufacturer accounts for login dropdown |
| `predict(data)` | POST | `/predict` | Predict by device ID |
| `searchDevices(q, limit)` | GET | `/devices` | Search devices by name or ID |
| `getManufacturers(q, limit)` | GET | `/manufacturers` | Manufacturer autocomplete |
| `getHistory(skip, limit)` | GET | `/predictions` | Paginated history |
| `getMetrics()` | GET | `/metrics` | Active model metrics |
| `getHealth()` | GET | `/health` | System health |
| `getMfrDashboard()` | GET | `/manufacturer/dashboard` | Manufacturer stats |
| `getMfrDevices(skip, limit, q)` | GET | `/manufacturer/devices` | Manufacturer's devices |
| `getMfrAlerts(skip, limit)` | GET | `/manufacturer/alerts` | Manufacturer's alerts |
| `markAlertRead(id)` | PATCH | `/manufacturer/alerts/{id}/read` | Mark alert read |

---

## Design Decisions

### Single global stylesheet (`index.css`)
All styles use CSS custom properties (`--teal`, `--red`, `--amber`, etc.). No CSS modules, no styled-components. Keeps the visual system consistent and easy to audit.

### Manufacturer dropdown: 200 on open, 60 on search
The login dropdown fetches all 3,952 manufacturer accounts once. Rendering all 3,952 items at once would hang the browser. The dropdown shows the first 200 alphabetically on open (scrollable), and filters to up to 60 matches as you type. This gives fast initial load and responsive search.

### JWT stored in localStorage
Simple and works naturally with React SPA. For production, consider `httpOnly` cookies to prevent XSS access to the token.

### Role-based routing in App.js, not per-page
Centralising role checks in `AppRoutes` means individual pages don't need to check auth — they can assume the correct user type has already been verified.

### Stat cards load from history + metrics, not a dedicated endpoint
`PredictPage` calls `GET /predictions?limit=200` and `GET /metrics` in parallel to populate the four stat cards. This avoids adding a `/stats` endpoint to the backend for a UI convenience feature.

### `low_confidence_flag` comes from the backend
The flag is set server-side (`confidence < 0.60`) and returned in the response. The frontend only displays the warn banner when `result.low_confidence_flag === true`.

---

## Running the Frontend

```bash
cd frontend
npm install
npm start
```

Runs at `http://localhost:3000`. Requires the backend to be running at `http://localhost:8000`.

To change the backend URL, edit the `baseURL` in `src/services/api.js`.
