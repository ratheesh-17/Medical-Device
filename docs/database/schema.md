# Database Schema

Database: `meddevice` (MySQL, InnoDB)

---

## Entity Relationship

```
manufacturers
     │
     │ manufacturer_id
     ↓
  devices
     │
     │ device_id
     ├──────────────────┐
     ↓                  ↓
  events           predictions


model_versions  (standalone — tracks trained model metadata)
```

---

## Tables

### manufacturers

| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | Manufacturer ID |
| name | VARCHAR(500) | Manufacturer name |
| country | VARCHAR(100) | Country of origin |

---

### devices

| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | Device ID |
| name | VARCHAR(500) | Device name |
| classification | VARCHAR(255) | Device category |
| description | TEXT | Device description |
| manufacturer_id | INT FK | → manufacturers.id |
| risk_class | VARCHAR(10) | FDA risk class: 1, 2, or 3 |
| implanted | VARCHAR(10) | YES / NO |
| country | VARCHAR(100) | Country |

---

### events

| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | Event ID |
| device_id | INT FK | → devices.id |
| action | TEXT | Action description |
| action_classification | VARCHAR(50) | Recall severity class |
| action_level | VARCHAR(100) | Action level |
| country | VARCHAR(100) | Country of event |
| event_date | DATETIME | Date of event |

---

### predictions

| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | Prediction ID |
| device_id | INT FK (nullable) | → devices.id |
| input_description | TEXT | User-provided description |
| input_classification | VARCHAR(255) | User-provided category |
| input_manufacturer | VARCHAR(500) | User-provided manufacturer |
| predicted_class | VARCHAR(10) | Predicted: I, II, or III |
| prob_class_1 | FLOAT | Probability for Class I |
| prob_class_2 | FLOAT | Probability for Class II |
| prob_class_3 | FLOAT | Probability for Class III |
| confidence | FLOAT | Max probability |
| low_confidence_flag | BOOLEAN | True if confidence < 0.60 |
| model_version | VARCHAR(100) | Model version used |
| created_at | DATETIME | Timestamp |

---

### model_versions

| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | Version ID |
| version_name | VARCHAR(100) UNIQUE | e.g. xgboost_v1 |
| algorithm | VARCHAR(100) | Algorithm name |
| macro_f1 | FLOAT | Macro-F1 score |
| precision_score | FLOAT | Weighted precision |
| recall_score | FLOAT | Weighted recall |
| is_active | BOOLEAN | Currently deployed model |
| trained_at | DATETIME | Training timestamp |
