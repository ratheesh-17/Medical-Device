# Setup & Deployment

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Backend + notebooks |
| MySQL | 8.0+ | Database |
| Node.js | 18+ | Frontend |
| Jupyter | Any | Running notebooks |

---

## Step 1 — Run the ML notebooks

The notebooks must run before the backend starts — they produce `model.pkl` and `pipeline.pkl`.

```bash
cd notebook
pip install -r ../backend/requirements.txt
jupyter notebook
```

Run in order:

1. `new_preprocessing_eda.ipynb` — produces `outputs/preprocessor.pkl`, `outputs/train.csv`, `outputs/test.csv`, `outputs/eda_summary.json`
2. `model_training.ipynb` — produces `backend/app/ml/model.pkl`, `backend/app/ml/pipeline.pkl`, `outputs/metrics.json`

---

## Step 2 — Set up MySQL

```sql
CREATE DATABASE meddevice CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'meddevice'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON meddevice.* TO 'meddevice'@'localhost';
FLUSH PRIVILEGES;
```

---

## Step 3 — Configure the backend

```bash
cd backend
cp .env.example .env
```

Edit `.env`:

```env
APP_NAME=MedDevice Risk Predictor
APP_VERSION=1.0.0

DB_HOST=localhost
DB_PORT=3306
DB_USER=meddevice
DB_PASSWORD=your_password
DB_NAME=meddevice

ALLOWED_ORIGINS=["http://localhost:3000"]

MODEL_PATH=app/ml/model.pkl
PIPELINE_PATH=app/ml/pipeline.pkl

SECRET_KEY=your-secret-key-change-in-prod
ACCESS_TOKEN_EXPIRE_MINUTES=480
ALERT_PROB_THRESHOLD=0.42
```

---

## Step 4 — Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

> **Note:** `requirements.txt` pins `bcrypt==4.0.1` (via `passlib[bcrypt]==1.7.4`). Newer bcrypt versions break passlib's CryptContext. Do not upgrade bcrypt independently.

---

## Step 5 — Seed the database

```bash
cd backend
python -m scripts.seed_db
```

Expected output:

```
Creating tables...
Loading CSVs...
  devices: (118249, 15), events: (124969, 30), manufacturers: (31827, 10)
  USA-only: 33657 devices, 35818 events
Seeding manufacturers...
  Inserted 31827 manufacturers.
Computing manufacturer_features (LOO)...
  Inserted 3952 manufacturer_features rows.
Computing classification_features...
  Inserted 17 classification_features rows.
Seeding devices (USA only)...
  Inserted 33657 devices.
Seeding model_versions from metrics.json...
  model_versions seeded.
Done.
```

Re-running is safe — it deletes and re-inserts all seeded data each time (delete order: Prediction → Device → ManufacturerFeatures → Manufacturer to respect FK constraints).

---

## Step 6 — Seed user accounts

```bash
cd backend
python -m scripts.seed_users
```

Expected output:

```
Hashing passwords...
Querying manufacturers...
Seeding 3952 manufacturer accounts + 1 user account...
Done. Seeded 3953 accounts.
  user      / user123
  mfr_<id>  / mfr123
```

This creates:
- 1 technician account: `user` / `user123`
- 3,952 manufacturer accounts: `mfr_<manufacturer_id>` / `mfr123` — one for every manufacturer with at least one USA device

> **Performance note:** Both passwords are hashed exactly once each, then the hash string is reused for all bulk inserts. This avoids 3,952 bcrypt operations and completes in seconds.

---

## Step 7 — Start the backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify it is healthy:

```bash
curl http://localhost:8000/api/v1/health
```

Expected:

```json
{
  "status": "ok",
  "service": "MedDevice Risk Predictor API",
  "db": "ok",
  "model": "loaded",
  "pipeline": "loaded"
}
```

Interactive API docs: `http://localhost:8000/docs`

---

## Step 8 — Start the frontend

```bash
cd frontend
npm install
npm start
```

Frontend runs at `http://localhost:3000`. You will be redirected to the login page.

**Demo credentials:**

| Role | Username | Password |
|---|---|---|
| Technician | `user` | `user123` |
| Manufacturer | `mfr_5247` (Boston Scientific) | `mfr123` |

---

## File locations after setup

```
Med-Device/
├── notebook/
│   ├── outputs/
│   │   ├── metrics.json           ← model metrics (read by seed_db + /metrics endpoint)
│   │   ├── eda_summary.json       ← dataset stats
│   │   ├── preprocessor.pkl       ← intermediate (not used by API directly)
│   │   └── train.csv / test.csv   ← intermediate splits
│   └── model_classes.py           ← ThresholdedClassifier source
│
└── backend/
    └── app/
        └── ml/
            ├── model.pkl          ← ThresholdedClassifier(XGBoost, threshold=0.42)
            ├── pipeline.pkl       ← ColumnTransformer (TF-IDF + OHE + Scaler)
            └── model_classes.py   ← must match notebook/model_classes.py
```

---

## Troubleshooting

**`status: degraded` / `model: not loaded`**
Model files are missing. Run both notebooks in order, then restart the server.

**`Access denied for user`**
Check `.env` DB credentials match your MySQL user.

**`ModuleNotFoundError: No module named 'model_classes'`**
The `sys.modules` alias in `prediction_service.py` handles this automatically at startup. Ensure `backend/app/ml/model_classes.py` exists and matches the notebook version.

**`Invalid credentials` after re-running `seed_db.py`**
`seed_db.py` does not touch the `users` table. If you wiped the DB entirely (e.g. `reset_db.py`), re-run `seed_users.py` to recreate all accounts.

**`seed_users.py` is slow**
Should not happen — passwords are hashed once and reused. If it is slow, check that `bcrypt==4.0.1` is installed (`pip show bcrypt`). Newer versions are incompatible with passlib.

**Prediction returns `503`**
Model not loaded. Check the `/health` endpoint and run notebooks if needed.

**`seed_db.py` crashes on FK constraint**
Delete order must be: Prediction → Device → ManufacturerFeatures → Manufacturer. The script handles this automatically. If you see FK errors, run `reset_db.py` first.
