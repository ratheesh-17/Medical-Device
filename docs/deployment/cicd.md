# CI/CD & Cloud Deployment

## Local Development

See [setup.md](setup.md) for full local setup instructions.

Quick start once set up:

```bash
# Terminal 1 — backend
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm start
```

---

## CI Pipeline (GitHub Actions)

The pipeline runs on every push and pull request to `main`.

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r backend/requirements.txt

      - name: Lint
        run: |
          pip install flake8
          flake8 backend/app --max-line-length=120

      - name: Type check
        run: |
          pip install mypy
          mypy backend/app --ignore-missing-imports

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "18"

      - name: Install and build
        run: |
          cd frontend
          npm ci
          npm run build
```

---

## Cloud Deployment (AWS)

### Recommended architecture

```
Route 53 (DNS)
     │
     ▼
Application Load Balancer
     │
     ├── ECS Fargate (FastAPI container)
     │        │
     │        └── ECR (Docker image registry)
     │
     └── S3 + CloudFront (React static build)
              │
              └── RDS MySQL (db.t3.micro)
```

### Backend — Docker

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY scripts/ ./scripts/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and push to ECR:

```bash
aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin <account>.dkr.ecr.ap-south-1.amazonaws.com

docker build -t meddevice-api ./backend
docker tag meddevice-api:latest <account>.dkr.ecr.ap-south-1.amazonaws.com/meddevice-api:latest
docker push <account>.dkr.ecr.ap-south-1.amazonaws.com/meddevice-api:latest
```

### Frontend — S3 + CloudFront

```bash
cd frontend
npm run build

aws s3 sync build/ s3://meddevice-frontend --delete
aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"
```

### Environment variables on ECS

Set these as ECS task environment variables or via AWS Secrets Manager:

```
DB_HOST=<rds-endpoint>
DB_PORT=3306
DB_USER=meddevice
DB_PASSWORD=<secret>
DB_NAME=meddevice
ALLOWED_ORIGINS=["https://your-cloudfront-domain.cloudfront.net"]
MODEL_PATH=app/ml/model.pkl
PIPELINE_PATH=app/ml/pipeline.pkl
SECRET_KEY=<strong-random-secret>
ACCESS_TOKEN_EXPIRE_MINUTES=480
ALERT_PROB_THRESHOLD=0.42
```

### RDS MySQL setup

```bash
aws rds create-db-instance \
  --db-instance-identifier meddevice-db \
  --db-instance-class db.t3.micro \
  --engine mysql \
  --engine-version 8.0 \
  --master-username meddevice \
  --master-user-password <password> \
  --allocated-storage 20 \
  --db-name meddevice
```

After RDS is ready, run seed from a bastion or ECS task:

```bash
python -m scripts.seed_db
python -m scripts.seed_users
```

---

## Model artifact deployment

`model.pkl` and `pipeline.pkl` are baked into the Docker image at build time. When a new model is trained:

1. Run both notebooks to regenerate artifacts
2. Rebuild and push the Docker image
3. Update the ECS service to deploy the new image
4. Re-run `seed_db.py` to update `model_versions` with new metrics
