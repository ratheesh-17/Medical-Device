# Setup & Deployment Guide

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| MySQL | 8.0+ |
| Jupyter Notebook / JupyterLab | Latest |

---

## 1. Clone & Install

```bash
git clone <repo-url>
cd Med-Device
```

---

## 2. Database Setup

```sql
CREATE DATABASE meddevice CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Tables are auto-created by SQLAlchemy on first backend startup — uncomment `Base.metadata.create_all` in `main.py`.

---

## 3. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt

copy .env.example .env         # Windows
# cp .env.example .env         # macOS/Linux
```

Edit `.env` with your MySQL credentials:

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=meddevice
```

---

## 4. ML Model Training

Run the notebooks **in order**:

### Step 1 — Preprocessing

```bash
cd notebook
jupyter notebook preprocessing.ipynb
```

Run all cells. Outputs:
- `notebook/outputs/train.csv`
- `notebook/outputs/test.csv`
- `backend/app/ml/pipeline.pkl`

### Step 2 — Model Training (v3)

```bash
jupyter notebook model_training_v3.ipynb
```

Run all cells. Outputs:
- `backend/app/ml/model.pkl`  ← `WeightedDecisionClassifier` wrapping XGBoost
- `backend/app/ml/pipeline.pkl`  ← updated copy
- `notebook/outputs/metrics.json`

> **Important:** `backend/app/ml/model_classes.py` must exist before loading any `.pkl` file. It defines `LabelOffsetClassifier` and `WeightedDecisionClassifier` — required for pickle deserialization.

---

## 5. Seed the Database

After running the notebooks (step 4), seed MySQL with manufacturer data and model metrics:

```bash
cd backend
python -m scripts.seed_db
```

This script:
- Loads the 3 raw CSVs into MySQL (`manufacturers`, `devices`, `events` tables)
- Computes `manufacturer_features` using the same aggregation logic as `preprocessing.ipynb`
- Seeds `model_versions` from `notebook/outputs/metrics.json`

---

## 6. Start the Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API: `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

---

## 6. Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend: `http://localhost:3000`

---

## 7. Verify Everything Works

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Manufacturer autocomplete (for React dropdown)
curl "http://localhost:8000/api/v1/manufacturers?q=medtronic"

# Test prediction
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"description": "Implantable cardiac pacemaker", "classification": "Cardiovascular Devices", "manufacturer_name": "Medtronic"}'
```
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| DB_HOST | localhost | MySQL host |
| DB_PORT | 3306 | MySQL port |
| DB_USER | root | MySQL username |
| DB_PASSWORD | *(empty)* | MySQL password |
| DB_NAME | meddevice | Database name |
| MODEL_PATH | app/ml/model.pkl | Path to model.pkl |
| PIPELINE_PATH | app/ml/pipeline.pkl | Path to pipeline.pkl |

---

## Startup Order

```
1. MySQL running
2. Backend started  (auto-creates tables)
3. Notebooks run    (exports .pkl files)
4. Backend restarted (loads new .pkl files)
5. Frontend started
```
