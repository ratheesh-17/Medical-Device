# main.py
# FastAPI application entry point

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import predict, history, metrics, health, manufacturers
from app.core.config import settings
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Medical Device Risk Class Prediction API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all: returns a consistent JSON error shape so the frontend has one error path."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(predict.router, prefix="/api/v1", tags=["Prediction"])
app.include_router(history.router, prefix="/api/v1", tags=["History"])
app.include_router(metrics.router, prefix="/api/v1", tags=["Metrics"])
app.include_router(manufacturers.router, prefix="/api/v1", tags=["Manufacturers"])
