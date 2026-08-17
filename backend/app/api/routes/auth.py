# api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.db_models import User
from app.core.security import verify_password, create_token, get_current_user

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    manufacturer_id: Optional[int] = None
    manufacturer_name: Optional[str] = None


@router.post("/auth/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_token({"sub": user.username, "role": user.role, "manufacturer_id": user.manufacturer_id})
    mfr_name = user.manufacturer.name if user.manufacturer else None
    return LoginResponse(
        access_token=token,
        role=user.role,
        username=user.username,
        manufacturer_id=user.manufacturer_id,
        manufacturer_name=mfr_name,
    )


@router.get("/auth/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "role": current_user.role,
        "manufacturer_id": current_user.manufacturer_id,
        "manufacturer_name": current_user.manufacturer.name if current_user.manufacturer else None,
    }


@router.get("/auth/manufacturers")
def list_mfr_accounts(db: Session = Depends(get_db)):
    """Returns all seeded manufacturer accounts with names for the login dropdown."""
    users = db.query(User).filter(User.role == "manufacturer").all()
    return [
        {
            "username": u.username,
            "manufacturer_id": u.manufacturer_id,
            "name": u.manufacturer.name if u.manufacturer else u.username,
        }
        for u in users
    ]
