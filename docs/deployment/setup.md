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
```

---

## Step 4 — Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

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
Seeding model_versions from metrics.json...
  model_versions seeded.
Done.
```

Re-running is safe — it deletes and re-inserts manufacturers, manufacturer_features, and model_versions each time.

---

## Step 6 — Start the backend

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

## Step 7 — Start the frontend

```bash
cd frontend
npm install
npm start
```

Frontend runs at `http://localhost:3000`.

---

## File locations after setup

```
Med-Device/
├── notebook/
│   ├── outputs/
│   │   ├── metrics.json           <- model metrics (read by seed_db + /metrics endpoint)
│   │   ├── eda_summary.json       <- dataset stats
│   │   ├── preprocessor.pkl       <- intermediate (not used by API directly)
│   │   └── train.csv / test.csv   <- intermediate (not used by API)
│   └── model_classes.py           <- ThresholdedClassifier source
│
└── backend/
    └── app/
        └── ml/
            ├── model.pkl          <- ThresholdedClassifier(XGBoost, threshold=0.42)
            ├── pipeline.pkl       <- ColumnTransformer (TF-IDF + OHE + Scaler)
            └── model_classes.py   <- must match notebook/model_classes.py
```

---

## Troubleshooting

**`status: degraded` / `model: not loaded`**
Model files are missing. Run both notebooks in order, then restart the server.

**`Access denied for user`**
Check `.env` DB credentials match your MySQL user.

**`ModuleNotFoundError: No module named 'model_classes'`**
The `sys.modules` alias in `prediction_service.py` handles this automatically at startup. Ensure `backend/app/ml/model_classes.py` exists and matches the notebook version.

**`seed_db.py` crashes on manufacturer insert**
The manufacturers CSV has no `country` column — this is expected and handled. The ORM `Manufacturer` model does not include a `country` field.

**Prediction returns `503`**
Model not loaded. Check the `/health` endpoint and run notebooks if needed.
