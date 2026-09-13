import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, hash_password
from app.models.user import User, RoleEnum

client = TestClient(app)

def _make_token(username="admin", role="Administrator"):
    return create_access_token(data={"sub": username, "role": role})

def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}

def _mock_user(username="admin", role=RoleEnum.ADMIN):
    return User(id=1, username=username, email=f"{username}@test.com",
                hashed_password="fakehash", role=role)

def _mock_auth(monkeypatch, username="admin", role=RoleEnum.ADMIN):
    """Mock the user lookup in deps.get_current_user to skip the DB entirely."""
    mock_user = _mock_user(username, role)
    monkeypatch.setattr("app.api.deps.get_user_by_username", lambda db, username: mock_user)

# --- Login API ---

def test_login_api_valid(monkeypatch):
    hashed = hash_password("correct_password")
    mock_user = User(id=1, username="admin", email="a@b.com", hashed_password=hashed, role=RoleEnum.ADMIN)
    
    monkeypatch.setattr("app.services.auth_service.get_user_by_username", lambda db, username: mock_user if username == "admin" else None)
    
    res = client.post("/auth/login", json={"username": "admin", "password": "correct_password"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_api_invalid_username(monkeypatch):
    monkeypatch.setattr("app.services.auth_service.get_user_by_username", lambda db, username: None)
    
    res = client.post("/auth/login", json={"username": "fake", "password": "pass"})
    assert res.status_code == 401

def test_login_api_invalid_password(monkeypatch):
    hashed = hash_password("correct_password")
    mock_user = User(id=1, username="admin", email="a@b.com", hashed_password=hashed, role=RoleEnum.ADMIN)
    
    monkeypatch.setattr("app.services.auth_service.get_user_by_username", lambda db, username: mock_user)
    
    res = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert res.status_code == 401

def test_login_api_malformed():
    res = client.post("/auth/login", json={"user": "admin"})
    assert res.status_code == 422

# --- Unauthenticated access → 401 ---

def test_unauthenticated_cases():
    res = client.get("/cases")
    assert res.status_code == 401

def test_unauthenticated_predict():
    res = client.post("/predict", json={"case_id": "C-1"})
    assert res.status_code == 401

def test_unauthenticated_alerts():
    res = client.get("/alerts")
    assert res.status_code == 401

# --- Invalid/missing token → 401 ---

def test_invalid_token_cases():
    res = client.get("/cases", headers={"Authorization": "Bearer garbage.token.here"})
    assert res.status_code == 401

# --- Health remains public ---

def test_health_no_auth():
    res = client.get("/health")
    assert res.status_code == 200

# --- Authenticated access with correct roles ---

def test_authenticated_cases(monkeypatch):
    _mock_auth(monkeypatch, "admin", RoleEnum.ADMIN)
    token = _make_token("admin", RoleEnum.ADMIN.value)
    
    from app.crud import crud_case
    monkeypatch.setattr(crud_case, "get_cases", lambda db, skip, limit: [])
    
    res = client.get("/cases", headers=_auth_header(token))
    assert res.status_code == 200

def test_authenticated_alerts(monkeypatch):
    _mock_auth(monkeypatch, "investigator", RoleEnum.LEA_INVESTIGATOR)
    token = _make_token("investigator", RoleEnum.LEA_INVESTIGATOR.value)
    
    from app.crud import crud_alert
    monkeypatch.setattr(crud_alert, "get_alerts", lambda db, skip, limit: [])
    
    res = client.get("/alerts", headers=_auth_header(token))
    assert res.status_code == 200

# --- RBAC: Analyst denied alert mutation → 403 ---

def test_analyst_cannot_mutate_alert(monkeypatch):
    _mock_auth(monkeypatch, "analyst", RoleEnum.I4C_ANALYST)
    token = _make_token("analyst", RoleEnum.I4C_ANALYST.value)
    
    res = client.patch("/alerts/1/status", json={"status": "RESOLVED"}, headers=_auth_header(token))
    assert res.status_code == 403

# --- RBAC: Investigator CAN mutate alert → allowed ---

def test_investigator_can_mutate_alert(monkeypatch):
    _mock_auth(monkeypatch, "investigator", RoleEnum.LEA_INVESTIGATOR)
    token = _make_token("investigator", RoleEnum.LEA_INVESTIGATOR.value)
    
    from app.crud import crud_alert
    from app.models.alert import Alert
    monkeypatch.setattr(crud_alert, "update_alert_status", lambda db, alert_id, status_in: Alert(id=1, case_id="C-1", priority="P1", status=status_in.status))
    
    res = client.patch("/alerts/1/status", json={"status": "IN_PROGRESS"}, headers=_auth_header(token))
    assert res.status_code == 200
