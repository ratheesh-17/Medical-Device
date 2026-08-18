# Roadmap & Development Status

Cognizant NPN AI Hackathon — Medical Device Risk Predictor

---

## Phase 1 — Data & ML Pipeline ✅ Complete

| Task | Status | Notes |
|---|---|---|
| Dataset exploration (ICIJ Implant Files) | ✅ | 3 CSVs: devices, events, manufacturers |
| USA-only scope decision | ✅ | `action_classification` + `determined_cause` only populated for USA |
| Label construction (risk score → binary failure) | ✅ | Class I recall = 3, Class II = 2, Class III = 1; cause bonus ±1 |
| Feature engineering (LOO manufacturer aggregates) | ✅ | Leave-one-out to prevent leakage |
| Preprocessing pipeline (TF-IDF + OHE + Scaler) | ✅ | 821-dim feature vector |
| Model selection (LR vs RF vs XGBoost) | ✅ | XGBoost selected: CV ROC-AUC 0.8551 |
| Threshold tuning (OOF search 0.30–0.71) | ✅ | Optimal threshold = 0.42 |
| Final test evaluation | ✅ | ROC-AUC 0.8553, F1 0.7528 |
| Artifact export (model.pkl, pipeline.pkl, metrics.json) | ✅ | Saved to `backend/app/ml/` |

---

## Phase 2 — Backend API ✅ Complete

| Task | Status | Notes |
|---|---|---|
| FastAPI project scaffold | ✅ | `app/main.py`, CORS, router registration |
| SQLAlchemy ORM models (9 tables) | ✅ | manufacturers, manufacturer_features, classification_features, devices, predictions, model_versions, device_risk_scores, users, alerts |
| Pydantic schemas | ✅ | DeviceLookupRequest, PredictResponse, PredictionRecord, ModelMetrics, ManufacturerItem, DeviceItem |
| `PredictionService` — ML inference | ✅ | Loads pkl once at startup; sys.modules alias for pickle resolution |
| `ManufacturerService` — DB feature lookup | ✅ | Fuzzy ILIKE search; safe defaults when not found |
| `HistoryService` — save + retrieve predictions | ✅ | Newest-first, paginated |
| `MetricsService` — model version query | ✅ | Returns active model from model_versions |
| `POST /predict` — device ID lookup | ✅ | Fetches device from DB, pulls features, runs model, creates alert |
| `GET /predictions` endpoint | ✅ | Pagination with skip/limit |
| `GET /metrics` + `GET /metrics/all` | ✅ | Active model + all versions |
| `GET /manufacturers` endpoint | ✅ | Autocomplete with q + limit params |
| `GET /devices` endpoint | ✅ | Search by name or ID |
| `GET /health` endpoint | ✅ | DB + model + pipeline status |
| JWT auth (`core/security.py`) | ✅ | create_token, decode_token, get_current_user, require_role |
| `POST /auth/login` | ✅ | bcrypt verify + JWT issue |
| `GET /auth/me` | ✅ | Returns current user info from token |
| `GET /auth/manufacturers` | ✅ | All manufacturer accounts sorted alphabetically |
| `GET /manufacturer/dashboard` | ✅ | Stats + classification breakdown (manufacturer-scoped) |
| `GET /manufacturer/devices` | ✅ | Paginated + searchable device list (manufacturer-scoped) |
| `GET /manufacturer/alerts` | ✅ | High-risk alerts (manufacturer-scoped) |
| `PATCH /manufacturer/alerts/{id}/read` | ✅ | Mark alert as read |
| Alert creation in predict route | ✅ | Only if prob_failure ≥ 0.42 AND manufacturer has User account |
| `seed_db.py` — database seeding | ✅ | 31,827 manufacturers, 33,657 USA devices, 3,952 features, 17 classification features, 1 model version |
| `seed_users.py` — user account seeding | ✅ | 1 technician + 3,952 manufacturer accounts; passwords hashed once and reused |
| `reset_db.py` — schema migration utility | ✅ | Drop + recreate all tables |
| bcrypt version fix | ✅ | Pinned to `bcrypt==4.0.1` for passlib compatibility |

---

## Phase 3 — Frontend ✅ Complete

| Task | Status | Notes |
|---|---|---|
| React project scaffold | ✅ | CRA, React Router |
| `AuthContext` — global auth state | ✅ | JWT in localStorage, session restore on mount |
| `LoginPage` — tab switcher | ✅ | Technician (fixed user) + Manufacturer (searchable dropdown) |
| Manufacturer dropdown performance | ✅ | 200 shown on open, 60 filtered on search — prevents render hang with 3,952 items |
| Role-based routing in `App.js` | ✅ | Unauthenticated → /login, manufacturer → /manufacturer, user → / |
| `PredictPage` — device ID lookup | ✅ | Device ID input, result panel with device info + prediction |
| `MfrDashboardPage` — manufacturer dashboard | ✅ | Stat cards, classification breakdown, devices tab, alerts tab |
| Alert mark-as-read | ✅ | PATCH call + unread count update |
| `HistoryPage` — prediction history table | ✅ | Paginated, newest first |
| `MetricsPage` — model performance panel | ✅ | ROC-AUC, F1, threshold display |
| `HealthPage` — system status | ✅ | DB, model, pipeline status |
| `Topbar` — role-aware navigation | ✅ | Different nav items per role + username + logout |
| `ConfidenceBar` component | ✅ | |
| `ProbabilityBars` component | ✅ | |
| `RiskBadge` component | ✅ | |
| `TopFeatures` component | ✅ | |
| `api.js` service layer | ✅ | All 14 endpoints + JWT interceptor |

---

## Phase 4 — Documentation ✅ Complete

| Document | Status |
|---|---|
| `README.md` | ✅ |
| `docs/ml/ml_pipeline.md` | ✅ |
| `docs/database/schema.md` | ✅ |
| `docs/api/api_reference.md` | ✅ |
| `docs/architecture.md` | ✅ |
| `docs/frontend/frontend.md` | ✅ |
| `docs/deployment/setup.md` | ✅ |
| `docs/deployment/cicd.md` | ✅ |
| `docs/roadmap.md` | ✅ |
| `docs/presentation.md` | ✅ |

---

## Phase 5 — Testing ✅ Complete

| Task | Status | Notes |
|---|---|---|
| Auth endpoints | ✅ | Login (user + manufacturer), /auth/me, invalid credentials → 401 |
| Device ID lookup | ✅ | Valid ID → prediction, invalid ID → 404 |
| Alert creation | ✅ | prob_failure ≥ 0.42 + registered manufacturer → alert created |
| Alert routing | ✅ | Alert visible only to correct manufacturer |
| Orphan alert prevention | ✅ | No alert created for manufacturers with no User account |
| Manufacturer dashboard | ✅ | Stats, devices, alerts all scoped to manufacturer_id |
| seed_users performance | ✅ | 3,953 accounts seeded in seconds (hash reuse) |
| bcrypt compatibility | ✅ | bcrypt==4.0.1 + passlib==1.7.4 |
| DB seeding | ✅ | seed_db.py + seed_users.py both clean |
| Prediction history persistence | ✅ | device_id FK saved correctly |
| Manufacturer dropdown | ✅ | 200 on open, 60 on search, no render hang |

---

## Effort Estimation

| Phase | Estimated | Actual |
|---|---|---|
| Data exploration + label design | 1 day | 1 day |
| Feature engineering + preprocessing | 1 day | 1 day |
| Model selection + threshold tuning | 1 day | 1 day |
| Backend scaffold + DB setup | 1 day | 1 day |
| All API endpoints + services | 1.5 days | 2 days |
| Auth system (JWT + bcrypt + roles) | 0.5 days | 1 day (bcrypt version issue) |
| Device seeding + ID lookup flow | 0.5 days | 0.5 days |
| Manufacturer dashboard + alerts | 1 day | 1 day |
| Frontend (pages + components + auth) | 2 days | 2 days |
| Documentation | 1 day | 1 day |
| Testing + bug fixes | 0.5 days | 0.5 days |
| **Total** | **~11 days** | **~11 days** |

---

## Known Limitations & Future Work

| Item | Priority | Notes |
|---|---|---|
| USA-only scope | Medium | `action_classification` / `determined_cause` not populated for non-USA devices. Expanding requires a different label strategy for international data. |
| `mfr_countries_all` always = 1.0 | Low | Constant feature for current dataset. Kept for schema completeness and future extensibility. |
| JWT in localStorage | Medium | Vulnerable to XSS. For production, use httpOnly cookies. |
| SECRET_KEY in .env | High | Must be changed to a strong random value before any public deployment. |
| Model retraining pipeline | Medium | Currently manual (re-run notebooks). Could be automated with Airflow or a scheduled ECS task. |
| Frontend test coverage | Low | No unit tests on React components. Add with React Testing Library. |
| Batch risk scoring | Low | `batch_predict.py` and `device_risk_scores` table exist but are not used in the current flow. Could pre-compute scores for all 33,657 devices for faster dashboard display. |
