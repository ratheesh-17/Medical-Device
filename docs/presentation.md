# Presentation Guide

Cognizant NPN AI Hackathon — Medical Device Risk Predictor

---

## Slide Structure (Suggested 8 slides)

### Slide 1 — Problem Statement
- Medical device failures cause patient harm and costly recalls
- The FDA receives thousands of Medical Device Reports (MDRs) annually
- **Gap:** No proactive risk signal at the point of device submission
- **Our solution:** Predict failure risk before a recall occurs, using manufacturer history + device description

### Slide 2 — Dataset
- Source: ICIJ Implant Files — global medical device recall and safety alert data
- 3 CSVs: 118,249 devices, 124,969 events, 31,827 manufacturers
- **USA-only scope:** `action_classification` and `determined_cause` — the fields needed to build a meaningful risk label — are only populated for USA devices
- USA subset: **33,662 devices, 35,826 events**

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
        │ HTTP/JSON
        ▼
FastAPI Backend (localhost:8000)
  ├── POST /predict  →  ManufacturerService (DB lookup)
  │                 →  PredictionService (pipeline.pkl + model.pkl)
  │                 →  HistoryService (persist result)
  ├── GET /predictions  →  paginated history
  ├── GET /metrics      →  model_versions table
  └── GET /manufacturers → autocomplete
        │ SQLAlchemy
        ▼
MySQL (meddevice DB)
  ├── manufacturers (31,827 rows)
  ├── manufacturer_features (3,952 rows — precomputed LOO aggregates)
  ├── predictions (runtime — every inference saved)
  └── model_versions (1 row — seeded from metrics.json)
```

### Slide 7 — Live Demo Flow
1. Open `http://localhost:3000`
2. Navigate to **Predict** page
3. Enter: description = *"Implantable cardiac pacemaker for rhythm management"*, classification = *"Cardiovascular Devices"*, manufacturer = *"Medtronic"*
4. Show prediction result: `predicted_failure`, `confidence`, `prob_failure`, `top_features`
5. Navigate to **History** — show the saved prediction
6. Navigate to **Metrics** — show ROC-AUC, F1, threshold
7. Navigate to **Health** — show all components green

### Slide 8 — Key Design Decisions (Talking Points)
- **Why binary, not 3-class?** Mentor guidance: "failure yes/no is more actionable." Binary label is cleaner and directly answers the clinical question.
- **Why USA-only?** Data quality — non-USA events have no `action_classification` / `determined_cause`. A model trained on that would learn country, not risk.
- **Why LOO for manufacturer features?** Prevents leakage — a device's own events can't influence its own manufacturer aggregate.
- **Why threshold 0.42?** In safety-critical domains, missing a true failure (false negative) is worse than a false alarm. Tuned threshold improves Failure recall 0.70 → 0.83.
- **Why precompute manufacturer features?** Joining 35k rows per inference request would be slow and risks training-serving skew. Precomputed once, served from DB.

---

## Demo Script

```
"Let me show you the system end-to-end."

[Open Predict page]
"A clinician or regulator enters a device description and selects the manufacturer.
 The backend looks up Medtronic's historical recall count from our database —
 31,827 manufacturers are indexed — and feeds that alongside the description
 into our XGBoost model."

[Submit prediction]
"The model returns a failure probability. Our threshold is 0.42, not the default 0.50,
 because in a safety-critical domain we'd rather flag a potential failure than miss one.
 You can see the top features that drove this prediction — in this case, the TF-IDF
 terms from the description and the manufacturer's event history."

[Open History page]
"Every prediction is saved. A safety team can audit all past assessments."

[Open Metrics page]
"Our model achieves ROC-AUC of 0.8553 and F1 of 0.7528 on the held-out test set.
 The threshold tuning alone improved Failure recall from 70% to 83%."
```

---

## Judge Q&A Preparation

**Q: Why not use device-level recall history as a feature?**
> Device-level history means we already know the device has been recalled — that's the answer, not a predictor. We deliberately excluded it. Manufacturer-level LOO is the correct abstraction: it captures the manufacturer's track record without leaking the device's own outcome.

**Q: How do you handle a brand-new manufacturer not in your database?**
> Safe defaults: `mfr_loo_event_count=0`, `mfr_countries_all=1`, `mfr_devices_all=0`. The model still runs — it just relies more heavily on the description and classification features. The `low_confidence_flag` will be set if confidence drops below 0.60.

**Q: Why USA-only? Doesn't that limit the model?**
> It's a data quality decision, not a modelling choice. The ICIJ dataset's `action_classification` and `determined_cause` fields — which we use to build the failure label — are only populated for USA devices. Training on other countries would mean learning which country filed the paperwork, not actual device risk. We document this limitation explicitly and it's a clear path for future work.

**Q: What's the business impact of the threshold choice?**
> At threshold 0.50, we miss 30% of true failures (recall 0.70). At 0.42, we miss only 17% (recall 0.83). The cost of a missed failure — patient harm, recall costs, regulatory action — far outweighs the cost of a false alarm that triggers additional review. The threshold is a business decision encoded in the model.

**Q: How would you deploy this in production?**
> FastAPI on ECS Fargate, React on S3 + CloudFront, RDS MySQL. Model artifacts baked into the Docker image. New model → rebuild image → update ECS service → re-run seed_db. Full CI/CD pipeline documented in `docs/deployment/cicd.md`.

**Q: How do you prevent the model from going stale?**
> The `model_versions` table tracks all trained models with timestamps. The `/metrics` endpoint always serves the active version. When new recall data arrives, re-run the notebooks, rebuild the Docker image, and update `is_active` in the DB. A monitoring job could track prediction distribution drift as a trigger for retraining.

**Q: What's the F1 score and why does it matter here?**
> F1 is the harmonic mean of precision and recall. We report it at both the default (0.50) and tuned (0.42) threshold so judges can see the trade-off explicitly. ROC-AUC is threshold-independent and shows the model's overall discriminative ability (0.8553). F1 at the operating threshold (0.7528) is what matters in practice.
