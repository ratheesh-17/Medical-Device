backend/
├── app/
│   ├── main.py                    # FastAPI app factory, CORS, router registration
│   ├── core/
│   │   ├── config.py              # env-based settings (pydantic-settings)
│   │   └── logging.py             # structured logging setup
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── router.py          # aggregates all route modules
│   │       ├── routes_predict.py  # POST /predict, POST /predict/batch
│   │       ├── routes_devices.py  # CRUD/list for devices + prediction history
│   │       └── routes_health.py   # GET /health, /health/model (model loaded? version?)
│   │
│   ├── schemas/                   # Pydantic request/response models
│   │   ├── predict.py             # PredictRequest, PredictResponse
│   │   └── device.py
│   │
│   ├── ml/
│   │   ├── model.pkl               # copied from your training notebook output
│   │   ├── pipeline.pkl
│   │   ├── model_classes.py        # ThresholdedClassifier definition (must match training)
│   │   └── predictor.py            # loads artifacts ONCE at startup, exposes predict(df)
│   │
│   ├── db/
│   │   ├── session.py              # SQLAlchemy engine + session factory
│   │   ├── models.py               # ORM tables: Device, PredictionLog, Manufacturer
│   │   └── base.py
│   │
│   ├── crud/
│   │   └── prediction.py           # insert/query prediction history
│   │
│   └── services/
│       └── prediction_service.py   # glue: request -> feature row -> predictor -> log to DB -> response
│
├── alembic/                        # DB migrations (versioned schema)
│   └── versions/
├── tests/
│   ├── test_predict_endpoint.py
│   └── test_predictor.py           # loads model.pkl fresh, asserts known input -> known output
│
├── Dockerfile
├── docker-compose.yml              # api + postgres, one command to spin up
├── requirements.txt
├── .env.example
└── README.md