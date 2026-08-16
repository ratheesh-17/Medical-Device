# Development Estimation & Roadmap

## Hackathon Build — What Was Delivered

| Phase | Work Done | Effort |
|-------|-----------|--------|
| Data exploration & preprocessing | EDA on 3 CSVs, feature engineering, train/test split, `preprocessing.ipynb` | ~1.5 days |
| Model training v1/v2 | Baseline models, CV selection, XGBoost winner, `LabelOffsetClassifier` | ~1 day |
| Model training v3 | Class imbalance diagnosis, OOF weight tuning, `WeightedDecisionClassifier`, Macro-F1: 0.74 → 0.80 | ~0.5 days |
| Backend API | FastAPI app, 4 routes, SQLAlchemy models, prediction service | ~1 day |
| Frontend | React UI — prediction form, results display, history, metrics | ~1.5 days |
| Documentation | API reference, ML pipeline, DB schema, setup guide, architecture | ~0.5 days |
| **Total** | | **~6 days** |

---

## Team Task Distribution

| Area | Owner(s) |
|------|---------|
| Data preprocessing & EDA | Data team (2) |
| ML model training & evaluation | ML team (2) |
| FastAPI backend | Backend team (2) |
| React frontend | Frontend team (2) |

---

## Immediate Next Steps (Post-Hackathon)

### Sprint 1 — Complete Core Integration (1 week)
- [ ] Activate `prediction_service.py` — uncomment model load + inference code
- [ ] Uncomment `Base.metadata.create_all` in `main.py` to auto-create DB tables
- [ ] Seed `model_versions` table with v3 metrics from `metrics.json`
- [ ] Wire frontend to all 4 API endpoints
- [ ] End-to-end smoke test: form → prediction → history → metrics

### Sprint 2 — Production Hardening (1 week)
- [ ] Add input sanitization and rate limiting to API
- [ ] Add structured logging (request ID, latency, predicted class)
- [ ] Add `/api/v1/metrics` seeding script from `metrics.json`
- [ ] Write unit tests for `PredictionService` and `WeightedDecisionClassifier`
- [ ] Add CI pipeline (GitHub Actions) — lint + test on push

### Sprint 3 — UX & Explainability (1 week)
- [ ] Add SHAP feature importance to prediction response
- [ ] Show confidence bar with color coding (green/yellow/red)
- [ ] Add batch prediction endpoint (`POST /api/v1/predict/batch`)
- [ ] Add CSV upload for bulk device assessment
- [ ] Improve history table — filters by class, date range, confidence

---

## Medium-Term Roadmap (1–3 months)

| Feature | Value | Effort |
|---------|-------|--------|
| Model retraining pipeline | Keep model fresh as new recall data arrives | High |
| Data drift monitoring | Alert when input distribution shifts from training data | Medium |
| MLflow integration | Experiment tracking, model registry, artifact versioning | Medium |
| Cloud deployment (AWS) | ECS/Fargate for API, RDS for MySQL, S3 for model artifacts | High |
| User authentication | Multi-user support, per-user prediction history | Medium |
| Feedback loop | Allow users to flag incorrect predictions → retrain data | High |
| REST API versioning | `/api/v2/` with backward compatibility | Low |

---

## Long-Term Vision (3–12 months)

- **Real-time data ingestion** — ingest new FDA recall events automatically via public API
- **Multi-country support** — extend beyond USA labels using semi-supervised learning
- **Regulatory reporting** — export prediction audit trails in FDA-compatible format
- **Mobile app** — field engineers can assess device risk on-site
- **Ensemble upgrade** — add LightGBM / CatBoost to the ensemble for further F1 gains

---

## Key Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Model degrades as recall data ages | Medium | High | Scheduled retraining pipeline |
| Class III recall still at 72% | High | High | More labeled data, SMOTE, cost-sensitive loss |
| MySQL single point of failure | Low | High | RDS Multi-AZ in production |
| Large model file slows cold start | Low | Medium | Model already 1.2 MB — acceptable |
| Frontend-backend CORS misconfiguration | Low | Medium | `ALLOWED_ORIGINS` env var, tested in CI |
