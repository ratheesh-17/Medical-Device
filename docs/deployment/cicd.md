# CI/CD & Cloud Deployment

---

## CI/CD Pipeline Design

### Tool: GitHub Actions

Two workflows — one for continuous integration (every push/PR), one for deployment (merge to main).

---

### Workflow 1 — CI (`.github/workflows/ci.yml`)

Triggers on every push and pull request to `main`.

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Lint
        run: |
          cd backend
          pip install flake8
          flake8 app/ --max-line-length=100

      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v
        env:
          DB_HOST: localhost
          DB_USER: root
          DB_PASSWORD: ""
          DB_NAME: meddevice_test

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: "18"

      - name: Install & build
        run: |
          cd frontend
          npm install
          npm run build
```

---

### Workflow 2 — Deploy (`.github/workflows/deploy.yml`)

Triggers on merge to `main` (after CI passes).

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    needs: []
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-south-1

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Build & push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/meddevice-backend:$IMAGE_TAG ./backend
          docker push $ECR_REGISTRY/meddevice-backend:$IMAGE_TAG

      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster meddevice-cluster \
            --service meddevice-backend \
            --force-new-deployment

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build React app
        run: |
          cd frontend
          npm install
          npm run build
        env:
          REACT_APP_API_URL: ${{ secrets.API_URL }}

      - name: Deploy to S3
        run: |
          aws s3 sync frontend/build/ s3://${{ secrets.S3_BUCKET }} --delete

      - name: Invalidate CloudFront cache
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CF_DISTRIBUTION_ID }} \
            --paths "/*"
```

---

## Docker Setup

### Backend Dockerfile (`backend/Dockerfile`)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (local dev with MySQL)

```yaml
version: "3.9"
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: ./backend/.env
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000

  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: password
      MYSQL_DATABASE: meddevice
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

---

## Cloud Deployment Architecture (AWS)

```
                        ┌─────────────────────┐
  Users ──── HTTPS ────▶│   CloudFront (CDN)  │
                        │   + S3 (React build) │
                        └──────────┬──────────┘
                                   │ API calls
                        ┌──────────▼──────────┐
                        │  Application Load   │
                        │     Balancer        │
                        └──────────┬──────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │     ECS Fargate Cluster      │
                    │  ┌──────────┐ ┌──────────┐  │
                    │  │ FastAPI  │ │ FastAPI  │  │
                    │  │ Task 1   │ │ Task 2   │  │
                    │  └────┬─────┘ └────┬─────┘  │
                    └───────┼────────────┼─────────┘
                            │            │
              ┌─────────────▼────────────▼──────────┐
              │           RDS MySQL                  │
              │        (Multi-AZ, encrypted)         │
              └──────────────────────────────────────┘
                            │
              ┌─────────────▼──────────────┐
              │   S3 Bucket (model store)  │
              │  model.pkl  pipeline.pkl   │
              └────────────────────────────┘
```

### AWS Services Used

| Service | Purpose |
|---------|---------|
| ECS Fargate | Run FastAPI containers — serverless, no EC2 management |
| ECR | Docker image registry |
| RDS MySQL (Multi-AZ) | Production database with automatic failover |
| S3 | Host React build + store model artifacts |
| CloudFront | CDN for frontend — low latency globally |
| ALB | Load balance across ECS tasks |
| Secrets Manager | Store DB credentials, injected as env vars into ECS tasks |
| CloudWatch | Logs and metrics for ECS tasks |

---

## Model Artifact Strategy

Model files (`model.pkl`, `pipeline.pkl`) are stored in S3 and downloaded by ECS tasks at startup:

```python
# In prediction_service.py _load() — production version
import boto3, tempfile, joblib, os

def _load(self):
    s3 = boto3.client("s3")
    bucket = os.getenv("MODEL_BUCKET", "meddevice-models")
    for key, attr in [("model.pkl", "model"), ("pipeline.pkl", "pipeline")]:
        with tempfile.NamedTemporaryFile() as f:
            s3.download_fileobj(bucket, key, f)
            setattr(self, attr, joblib.load(f.name))
```

This means model updates don't require a new Docker image — just upload new `.pkl` files to S3 and restart the ECS service.

---

## Deployment Environments

| Environment | Trigger | Infrastructure |
|-------------|---------|----------------|
| Local | Manual (`uvicorn --reload`) | Docker Compose |
| Staging | Push to `develop` branch | ECS Fargate (1 task, smaller RDS) |
| Production | Merge to `main` | ECS Fargate (2+ tasks, RDS Multi-AZ) |

---

## GitHub Secrets Required

| Secret | Value |
|--------|-------|
| `AWS_ACCESS_KEY_ID` | IAM user with ECS/ECR/S3 permissions |
| `AWS_SECRET_ACCESS_KEY` | Corresponding secret |
| `API_URL` | Production API base URL |
| `S3_BUCKET` | Frontend S3 bucket name |
| `CF_DISTRIBUTION_ID` | CloudFront distribution ID |
