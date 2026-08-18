# api/routes/predict.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.schemas.schemas import DeviceLookupRequest, PredictRequest, PredictResponse
from app.services.prediction_service import prediction_service
from app.services.history_service import save_prediction
from app.services.manufacturer_service import get_manufacturer_features, get_classification_features
from app.models.db_models import Device, Alert
from app.core.security import decode_token
from app.database import get_db
from app.core.config import settings

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


@router.post("/predict", response_model=PredictResponse)
def predict(
    request: DeviceLookupRequest,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    try:
        device = db.query(Device).filter(Device.id == request.device_id).first()
        if device is None:
            raise HTTPException(status_code=404, detail=f"Device ID {request.device_id} not found in USA dataset.")

        mfr_name = device.manufacturer.name if device.manufacturer else ""
        mfr_features = get_manufacturer_features(db, mfr_name)
        clf_features = get_classification_features(db, device.classification or "")

        result = prediction_service.predict(
            description=device.description or "",
            classification=device.classification or "",
            known_prior_incidents=request.known_prior_incidents,
            **mfr_features,
            **clf_features,
        )

        result["device_id"] = device.id
        result["device_name"] = device.name
        result["device_description"] = device.description
        result["device_classification"] = device.classification
        result["manufacturer_name"] = mfr_name

        response = PredictResponse(**result, model_version=settings.APP_VERSION)

        # Determine who triggered this prediction
        triggered_by = "anonymous"
        if credentials:
            payload = decode_token(credentials.credentials)
            triggered_by = payload.get("sub", "anonymous")

        # Auto-create alert only if high risk AND the manufacturer has a registered account
        if result["prob_failure"] >= settings.ALERT_PROB_THRESHOLD and device.manufacturer_id:
            from app.models.db_models import User
            mfr_user = db.query(User).filter(
                User.manufacturer_id == device.manufacturer_id,
                User.role == "manufacturer",
            ).first()
            if mfr_user:
                alert = Alert(
                    device_id=device.id,
                    manufacturer_id=device.manufacturer_id,
                    prob_failure=result["prob_failure"],
                    predicted_label=result["predicted_label"],
                    triggered_by=triggered_by,
                    status="unread",
                )
                db.add(alert)

        log_req = PredictRequest(
            device_id=device.id,
            description=device.description or "",
            classification=device.classification or "",
            manufacturer_name=mfr_name,
            device_name=device.name,
            known_prior_incidents=request.known_prior_incidents,
        )
        save_prediction(db, log_req, response)
        db.commit()
        return response
    except HTTPException:
        raise
    except NotImplementedError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
