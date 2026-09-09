from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.auth import LoginRequest, TokenResponse
from app.services import auth_service

router = APIRouter()

@router.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(deps.get_db)):
    """
    Authenticate a user and return a JWT access token.
    """
    return auth_service.authenticate_user(db, request)
