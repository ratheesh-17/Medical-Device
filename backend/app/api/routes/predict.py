# api/routes/predict.py
# POST /api/v1/predict — accepts device info, returns risk class prediction

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.schemas import PredictRequest, PredictResponse
from app.services.prediction_service import prediction_service
from app.services.history_service import save_prediction
from app.database import get_db
from app.core.config import settings

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest, db: Session = Depends(get_db)):
    try:
        result = prediction_service.predict(
            description=request.description,
            classification=request.classification,
            manufacturer_name=request.manufacturer_name or "",
        )
        response = PredictResponse(
            **result,
            model_version=settings.APP_VERSION,
        )
        save_prediction(db, request, response)
        return response
    except NotImplementedError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
