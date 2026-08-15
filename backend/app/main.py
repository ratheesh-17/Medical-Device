# main.py
# FastAPI application entry point
# Registers all routers and starts the app

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import predict, history, metrics, health
from app.core.config import settings
from app.database import engine, Base

# TODO: Create all DB tables on startup
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Medical Device Risk Class Prediction API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(predict.router, prefix="/api/v1", tags=["Prediction"])
app.include_router(history.router, prefix="/api/v1", tags=["History"])
app.include_router(metrics.router, prefix="/api/v1", tags=["Metrics"])
