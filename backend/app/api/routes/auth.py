from fastapi import APIRouter
from app.schemas.auth import LoginRequest

router = APIRouter()

@router.post("/auth/login")
def login(request: LoginRequest):
    return {"status": "stub", "token": "mock-jwt-token"}
