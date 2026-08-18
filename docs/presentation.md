# Presentation Guide

Cognizant NPN AI Hackathon — SentryMed: Medical Device Risk Predictor

---

## Slide Structure (Suggested 9 slides)

### Slide 1 — Problem Statement
- Medical device failures cause patient harm and costly recalls
- The FDA receives thousands of Medical Device Reports (MDRs) annually
- **Gap:** No proactive risk signal at the point of device assessment
- **Our solution:** SentryMed — predict failure risk before a recall occurs, using manufacturer history + device description. Alert manufacturers in real time.

### Slide 2 — Dataset
- Source: ICIJ Implant Files — global medical device recall and safety alert data
- 3 CSVs: 118,249 devices, 124,969 events, 31,827 manufacturers
- **USA-only scope:** `action_classification` and `determined_cause` — the fields needed to build a meaningful risk label — are only populated for USA devices
- USA subset: **33,657 devices, 35,818 events**

### Slide 3 — Label Design
- Binary target: **Failure (1) / No Failure (0)**
- Risk score = `severity(action_classification)` + `cause_bonus(determined_cause)`
  - Class I recall (most severe) = 3, Class II = 2, Class III = 1
  - Genuine technical/design/material cause = +1, administrative = −1
- Device label = max risk score across all its events ≥ 3 → Failure
- **Class balance:** 54% No Failure / 46% Failure — no oversampling needed

### Slide 4 — Features & Leakage Discipline
| Feature | Type | Why included |
|---|---|---|
| `description` | Text (TF-IDF) | Primary signal — what the device does |
| `classification` | Categorical (OHE) | FDA device category |
| `mfr_loo_event_count` | Numeric | Manufacturer's recall history (LOO) |
| `mfr_countries_all` | Numeric | Manufacturer's geographic footprint |
| `mfr_devices_all` | Numeric | Manufacturer's device portfolio size |
| `description_len` | Numeric | Proxy for documentation quality |
| `classification_prior_count` | Numeric | Historical event activity in this category |
| `event_year` | Numeric | Controls for reporting-era confound |

- `action_classification` and `determined_cause` are **excluded** — they define the label, not the input
- Manufacturer aggregates use **leave-one-out** — each device's own events excluded from its manufacturer's aggregate

### Slide 5 — Model & Results
- 3 candidates evaluated via 5-fold CV: Logistic Regression, Random Forest, **XGBoost** ← selected
- Threshold tuned on out-of-fold predictions (0.30–0.71 search) → **0.42**

| Metric | Value |
|---|---|
| Test ROC-AUC | **0.8553** |
| F1 at tuned threshold (0.42) | **0.7528** |
| F1 at default threshold (0.50) | 0.7308 |
| Failure Recall (tuned) | **0.83** |

- Tuning threshold 0.50 → 0.42 improves Failure recall 0.70 → **0.83** — the right trade-off for safety-critical applications

### Slide 6 — System Architecture
```
React Frontend (localhost:3000)
  LoginPage (Technician / Manufacturer tabs)
  PredictPage → device ID lookup
  MfrDashboardPage → alerts + device portfolio
        │ HTTP/JSON + JWT Bearer
        ▼
FastAPI Backend (localhost:8000)
  POST /predict  →  Device DB lookup
                 →  ManufacturerService (precomputed features)
                 →  PredictionService (pipeline.pkl + model.pkl)
                 →  Alert creation (if prob ≥ 0.42 + mfr has account)
  GET /manufacturer/dashboard → scoped to manufacturer_id
  POST /auth/login → JWT issue
        │ SQLAlchemy
        ▼
MySQL (meddevice DB)
  manufacturers (31,827)  │  devices (33,657 USA)
  manufacturer_features (3,952)  │  classification_features (17)
  predictions (runtime)  │  model_versions (1)
  users (3,953)  │  alerts (runtime)
```

### Slide 7 — Auth & Alert System
- **Two roles:** Technician (`user`) and Manufacturer (`mfr_<id>`)
- **3,952 manufacturer accounts** seeded — one for every manufacturer with ≥1 USA device
- **Alert routing:** When a technician predicts `prob_failure ≥ 0.42`, an alert is automatically created and routed to the device's manufacturer
- **Orphan alert prevention:** Alert only created if the manufacturer has a registered account
- **Manufacturer dashboard:** Real-time view of unread alerts, device portfolio, classification breakdown

### Slide 8 — Live Demo Flow
1. Open `http://localhost:3000` → Login page
2. **Technician login:** tab = Technician, user/user123 → Predict page
3. Enter device ID `16284` → Submit
4. Show prediction result: device name, manufacturer, `predicted_failure`, `confidence`, `prob_failure`, `top_features`
5. Navigate to **History** — show the saved prediction
6. Navigate to **Metrics** — show ROC-AUC, F1, threshold
7. **Manufacturer login:** tab = Manufacturer, search "Boston Scientific" → select → mfr123
8. Show **Dashboard** — stat cards, classification breakdown, Alerts tab with the alert just created

### Slide 9 — Key Design Decisions
- **Why device ID lookup?** Eliminates input errors, ties predictions to auditable records, ensures model receives exact training-data descriptions
- **Why USA-only?** Data quality — non-USA events have no `action_classification` / `determined_cause`. A model trained on that would learn country, not risk.
- **Why LOO for manufacturer features?** Prevents leakage — a device's own events can't influence its own manufacturer aggregate.
- **Why threshold 0.42?** Failure recall 0.70 → 0.83. Missing a true failure is worse than a false alarm.
- **Why alert only if manufacturer has account?** Prevents orphan alerts accumulating for manufacturers that will never log in.

---

## Demo Script

```
"Let me show you SentryMed end-to-end."

[Open Login page]
"There are two roles — technicians who assess devices, and manufacturers who
 receive alerts. Let me log in as a technician first."

[Technician login → Predict page]
"A technician enters a device ID from the ICIJ dataset. The backend looks up
 the device, fetches Boston Scientific's historical recall count from our
 database — 31,827 manufacturers are indexed — and feeds that alongside the
 device description into our XGBoost model."

[Enter device ID 16284 → Submit]
"The model returns a failure probability. Our threshold is 0.42, not the
 default 0.50, because in a safety-critical domain we'd rather flag a
 potential failure than miss one. You can see the top features that drove
 this prediction — TF-IDF terms from the description and the manufacturer's
 event history."

[Open History page]
"Every prediction is saved. A safety team can audit all past assessments."

[Open Metrics page]
"Our model achieves ROC-AUC of 0.8553 and F1 of 0.7528 on the held-out
 test set. The threshold tuning alone improved Failure recall from 70% to 83%."

[Logout → Manufacturer login → search Boston Scientific → Dashboard]
"Now let me log in as the manufacturer. The dashboard shows their device
 portfolio, classification breakdown, and — here — the alert that was just
 created when the technician predicted that device. The manufacturer can
 see the device name, failure probability, and which technician triggered it."
```

---

## Judge Q&A Preparation

**Q: Why device ID lookup instead of free-form input?**
> Free-form input introduces user error — a typo in the description changes the TF-IDF features. Device ID lookup ensures the model always receives the exact description from the training data, ties predictions to auditable records, and eliminates the need for the user to know model internals.

**Q: Why not use device-level recall history as a feature?**
> Device-level history means we already know the device has been recalled — that's the answer, not a predictor. We deliberately excluded it. Manufacturer-level LOO is the correct abstraction: it captures the manufacturer's track record without leaking the device's own outcome.

**Q: How do you handle a brand-new manufacturer not in your database?**
> Safe defaults: `mfr_loo_event_count=0`, `mfr_countries_all=1`, `mfr_devices_all=0`. The model still runs — it relies more heavily on the description and classification features. The `low_confidence_flag` will be set if confidence drops below 0.60.

**Q: Why USA-only? Doesn't that limit the model?**
> It's a data quality decision, not a modelling choice. The ICIJ dataset's `action_classification` and `determined_cause` fields — which we use to build the failure label — are only populated for USA devices. Training on other countries would mean learning which country filed the paperwork, not actual device risk. We document this limitation explicitly.

**Q: What's the business impact of the threshold choice?**
> At threshold 0.50, we miss 30% of true failures (recall 0.70). At 0.42, we miss only 17% (recall 0.83). The cost of a missed failure — patient harm, recall costs, regulatory action — far outweighs the cost of a false alarm that triggers additional review.

**Q: How does the alert system work?**
> When a technician predicts a device with `prob_failure ≥ 0.42`, the backend checks if the device's manufacturer has a registered account. If yes, an alert is created and routed to that manufacturer's dashboard. We check for a registered account first to prevent orphan alerts accumulating for manufacturers that will never log in.

**Q: How would you deploy this in production?**
> FastAPI on ECS Fargate, React on S3 + CloudFront, RDS MySQL. Model artifacts baked into the Docker image. New model → rebuild image → update ECS service → re-run seed_db. Full CI/CD pipeline documented in `docs/deployment/cicd.md`.

**Q: How do you prevent the model from going stale?**
> The `model_versions` table tracks all trained models with timestamps. The `/metrics` endpoint always serves the active version. When new recall data arrives, re-run the notebooks, rebuild the Docker image, and update `is_active` in the DB.

**Q: What's the F1 score and why does it matter here?**
> F1 is the harmonic mean of precision and recall. We report it at both the default (0.50) and tuned (0.42) threshold so judges can see the trade-off explicitly. ROC-AUC is threshold-independent and shows the model's overall discriminative ability (0.8553). F1 at the operating threshold (0.7528) is what matters in practice.
