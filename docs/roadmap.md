# Roadmap & Development Estimation

Cognizant NPN AI Hackathon — Medical Device Risk Predictor

---

## Project Phases

### Phase 1 — Data & ML Pipeline ✅ Complete

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

### Phase 2 — Backend API ✅ Complete

| Task | Status | Notes |
|---|---|---|
| FastAPI project scaffold | ✅ | `app/main.py`, CORS, router registration |
| SQLAlchemy ORM models (5 tables) | ✅ | manufacturers, manufacturer_features, devices, predictions, model_versions |
| Pydantic schemas | ✅ | PredictRequest, PredictResponse, PredictionRecord, ModelMetrics, ManufacturerItem |
| `PredictionService` — ML inference | ✅ | Loads pkl once at startup; sys.modules alias for pickle resolution |
| `ManufacturerService` — DB feature lookup | ✅ | Fuzzy ILIKE search; safe defaults when not found |
| `HistoryService` — save + retrieve predictions | ✅ | Newest-first, paginated |
| `MetricsService` — model version query | ✅ | Returns active model from model_versions |
| `POST /predict` endpoint | ✅ | Full inference + persist flow |
| `GET /predictions` endpoint | ✅ | Pagination with skip/limit |
| `GET /metrics` + `GET /metrics/all` | ✅ | Active model + all versions |
| `GET /manufacturers` endpoint | ✅ | Autocomplete with q + limit params |
| `GET /health` endpoint | ✅ | DB + model + pipeline status |
| `seed_db.py` — database seeding | ✅ | 31,827 manufacturers, 3,952 features, 1 model version |
| `reset_db.py` — schema migration utility | ✅ | Drop + recreate all tables |
| `.env` configuration | ✅ | DB, model paths, CORS origins, app version |

---

### Phase 3 — Frontend ✅ Complete

| Task | Status | Notes |
|---|---|---|
| React project scaffold | ✅ | CRA, React Router |
| `PredictPage` — prediction form | ✅ | Description, classification, manufacturer autocomplete, device name |
| `HistoryPage` — prediction history table | ✅ | Paginated, newest first |
| `MetricsPage` — model performance panel | ✅ | ROC-AUC, F1, threshold display |
| `HealthPage` — system status | ✅ | DB, model, pipeline status |
| `ConfidenceBar` component | ✅ | Visual confidence indicator |
| `ProbabilityBars` component | ✅ | P(failure) vs P(no failure) bars |
| `RiskBadge` component | ✅ | Failure / No Failure badge |
| `TopFeatures` component | ✅ | Top 5 influential features |
| `Topbar` component | ✅ | Navigation |
| `api.js` service layer | ✅ | Axios calls to all 6 endpoints |

---

### Phase 4 — Documentation ✅ Complete

| Document | Status |
|---|---|
| `docs/ml/ml_pipeline.md` | ✅ |
| `docs/database/schema.md` | ✅ |
| `docs/api/api_reference.md` | ✅ |
| `docs/architecture.md` | ✅ |
| `docs/deployment/setup.md` | ✅ |
| `docs/deployment/cicd.md` | ✅ |
| `docs/roadmap.md` | ✅ |
| `docs/presentation.md` | ✅ |
| `README.md` | ✅ |

---

### Phase 5 — Testing ✅ Complete

| Task | Status | Notes |
|---|---|---|
| All 12 API endpoint tests | ✅ | Passed — see test results below |
| DB migration + re-seed verification | ✅ | reset_db.py + seed_db.py both clean |
| Prediction history persistence | ✅ | Pagination verified (skip/limit) |
| Validation error handling | ✅ | 422 on short description, missing fields |
| Manufacturer not found fallback | ✅ | Defaults used, prediction still returns |

**Endpoint test results:**

| Test | Result |
|---|---|
| `GET /health` | `{"status":"ok","db":"ok","model":"loaded","pipeline":"loaded"}` ✅ |
| `GET /metrics` | `{"roc_auc":0.8553,"f1_tuned":0.7528,"f1_default":0.7308,"threshold":0.42}` ✅ |
| `GET /metrics/all` | Array with 1 version ✅ |
| `GET /manufacturers?q=medtronic&limit=5` | 5 fuzzy-matched results ✅ |
| `POST /predict` (Medtronic, cardiac pacemaker) | `predicted_failure: false, confidence: 0.7593` ✅ |
| `POST /predict` (DePuy, ASR Hip) | `predicted_failure: false, confidence: 0.7899` ✅ |
| `POST /predict` (no manufacturer) | Uses defaults, valid prediction ✅ |
| `POST /predict` (description < 5 chars) | `422 string_too_short` ✅ |
| `POST /predict` (missing description) | `422 Field required` ✅ |
| `GET /predictions` | 5 records, newest first ✅ |
| `GET /predictions?skip=0&limit=2` | First 2 records ✅ |
| `GET /predictions?skip=2&limit=2` | Next 2 records (pagination) ✅ |

---

## Effort Estimation

| Phase | Estimated | Actual |
|---|---|---|
| Data exploration + label design | 1 day | 1 day |
| Feature engineering + preprocessing | 1 day | 1 day |
| Model selection + threshold tuning | 1 day | 1 day |
| Backend scaffold + DB setup | 1 day | 1 day |
| All 6 API endpoints + services | 1.5 days | 2 days (DB schema bug + migration) |
| Frontend (4 pages + 5 components) | 1.5 days | 1.5 days |
| Documentation | 1 day | 1 day |
| Testing + bug fixes | 0.5 days | 0.5 days |
| **Total** | **~8.5 days** | **~9 days** |

---

## Known Limitations & Future Work

| Item | Priority | Notes |
|---|---|---|
| USA-only scope | Medium | `action_classification` / `determined_cause` not populated for non-USA devices. Expanding requires a different label strategy for international data. |
| `mfr_countries_all` always = 1.0 | Low | Constant feature for current dataset. Kept for schema completeness and future extensibility when non-USA data is added. |
| Device-level history excluded | By design | Device history = knowing the answer (leakage). Manufacturer-level LOO is the correct abstraction. |
| No authentication on API | Medium | Add JWT or API key auth before any public deployment. |
| Model retraining pipeline | Medium | Currently manual (re-run notebooks). Could be automated with Airflow or a scheduled ECS task. |
| Frontend test coverage | Low | No unit tests on React components. Add with React Testing Library. |
