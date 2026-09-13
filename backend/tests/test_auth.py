import pytest
from fastapi import HTTPException
from datetime import timedelta
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.services.auth_service import authenticate_user
from app.schemas.auth import LoginRequest
from app.models.user import User, RoleEnum

# --- Password Hashing ---

def test_hash_and_verify_password():
    hashed = hash_password("testpass123")
    assert hashed != "testpass123"
    assert verify_password("testpass123", hashed)
    assert not verify_password("wrongpass", hashed)

# --- JWT ---

def test_create_and_decode_token():
    token = create_access_token(data={"sub": "testuser", "role": "Administrator"})
    payload = decode_access_token(token)
    assert payload["sub"] == "testuser"
    assert payload["role"] == "Administrator"

def test_expired_token():
    token = create_access_token(
        data={"sub": "testuser"},
        expires_delta=timedelta(seconds=-1)
    )
    from jose import ExpiredSignatureError
    with pytest.raises(ExpiredSignatureError):
        decode_access_token(token)

def test_invalid_token():
    from jose import JWTError
    with pytest.raises(JWTError):
        decode_access_token("not.a.valid.token")

# --- Auth Service ---

def test_authenticate_valid_user(monkeypatch):
    hashed = hash_password("correct_password")
    mock_user = User(id=1, username="admin", email="a@b.com", hashed_password=hashed, role=RoleEnum.ADMIN)
    
    monkeypatch.setattr("app.services.auth_service.get_user_by_username", lambda db, username: mock_user if username == "admin" else None)
    
    result = authenticate_user(None, LoginRequest(username="admin", password="correct_password"))
    assert result.access_token
    assert result.token_type == "bearer"

def test_authenticate_invalid_username(monkeypatch):
    monkeypatch.setattr("app.services.auth_service.get_user_by_username", lambda db, username: None)
    
    with pytest.raises(HTTPException) as exc:
        authenticate_user(None, LoginRequest(username="nonexistent", password="anything"))
    assert exc.value.status_code == 401

def test_authenticate_invalid_password(monkeypatch):
    hashed = hash_password("correct_password")
    mock_user = User(id=1, username="admin", email="a@b.com", hashed_password=hashed, role=RoleEnum.ADMIN)
    
    monkeypatch.setattr("app.services.auth_service.get_user_by_username", lambda db, username: mock_user)
    
    with pytest.raises(HTTPException) as exc:
        authenticate_user(None, LoginRequest(username="admin", password="wrong_password"))
    assert exc.value.status_code == 401
