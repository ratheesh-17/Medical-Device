# Setup & Deployment Guide

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- Jupyter Notebook / JupyterLab

---

## 1. Database Setup

```sql
CREATE DATABASE meddevice CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Tables are auto-created by SQLAlchemy on first backend startup (uncomment `Base.metadata.create_all` in `main.py`).

---

## 2. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Copy and fill in your credentials
copy .env.example .env

# Start the API
uvicorn app.main:app --reload --port 8000
```

API will be available at: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

---

## 3. ML Model Training

```bash
cd notebook
jupyter notebook model_training.ipynb
```

Run all cells. The final cells export:
- `backend/app/ml/pipeline.pkl`
- `backend/app/ml/model.pkl`

Restart the backend after exporting.

---

## 4. Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend will be available at: `http://localhost:3000`

---

## 5. Verify Everything Works

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Test prediction
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"description": "Implantable cardiac pacemaker", "classification": "Cardiovascular Devices"}'
```

---

## Environment Variables Reference

| Variable | Description |
|----------|-------------|
| DB_HOST | MySQL host (default: localhost) |
| DB_PORT | MySQL port (default: 3306) |
| DB_USER | MySQL username |
| DB_PASSWORD | MySQL password |
| DB_NAME | Database name (default: meddevice) |
| MODEL_PATH | Path to model.pkl |
| PIPELINE_PATH | Path to pipeline.pkl |
