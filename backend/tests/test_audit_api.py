import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User, RoleEnum
from app.core.security import hash_password, create_access_token

client = TestClient(app)

class MockAuditLogger:
    def __init__(self):
        self.logs = []
    
    def mock_create_audit_log(self, db, audit_in):
        self.logs.append(audit_in.model_dump())
        return audit_in

@pytest.fixture
def audit_logger(monkeypatch):
    logger = MockAuditLogger()
    monkeypatch.setattr("app.services.audit_service.create_audit_log", logger.mock_create_audit_log)
    return logger

def _mock_user(username="admin", role=RoleEnum.ADMIN):
    return User(id=1, username=username, email=f"{username}@test.com",
                hashed_password=hash_password("password"), role=role)

def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}

def test_successful_login_audit(monkeypatch, audit_logger):
    mock_user = _mock_user()
    monkeypatch.setattr("app.services.auth_service.get_user_by_username", lambda db, username: mock_user if username == "admin" else None)
    
    res = client.post("/auth/login", data={"username": "admin", "password": "password"})
    assert res.status_code == 200
    
    assert len(audit_logger.logs) == 1
    log = audit_logger.logs[0]
    assert log["action"] == "LOGIN"
    assert log["status"] == "SUCCESS"
    assert log["user_id"] == 1
    assert "password" not in log["resource"]

def test_failed_login_audit(monkeypatch, audit_logger):
    monkeypatch.setattr("app.services.auth_service.get_user_by_username", lambda db, username: None)
    
    res = client.post("/auth/login", data={"username": "wronguser", "password": "wrongpassword"})
    assert res.status_code == 401
    
    assert len(audit_logger.logs) == 1
    log = audit_logger.logs[0]
    assert log["action"] == "LOGIN"
    assert log["status"] == "FAILED"
    assert log["user_id"] is None
    assert "wrongpassword" not in log["resource"]
    assert "username:wronguser" in log["resource"]

def test_failed_login_wrong_password_audit(monkeypatch, audit_logger):
    mock_user = _mock_user()
    monkeypatch.setattr("app.services.auth_service.get_user_by_username", lambda db, username: mock_user if username == "admin" else None)
    
    res = client.post("/auth/login", data={"username": "admin", "password": "wrongpassword"})
    assert res.status_code == 401
    
    assert len(audit_logger.logs) == 1
    log = audit_logger.logs[0]
    assert log["action"] == "LOGIN"
    assert log["status"] == "FAILED"
    assert log["user_id"] == 1
    assert "wrongpassword" not in log["resource"]

def test_case_access_audit(monkeypatch, audit_logger):
    mock_user = _mock_user()
    monkeypatch.setattr("app.api.deps.get_user_by_username", lambda db, username: mock_user)
    
    from app.crud import crud_case
    monkeypatch.setattr(crud_case, "get_cases", lambda db, skip, limit: [])
    
    token = create_access_token({"sub": "admin", "role": "Administrator"})
    res = client.get("/cases", headers=_auth_header(token))
    
    assert res.status_code == 200
    assert len(audit_logger.logs) == 1
    assert audit_logger.logs[0]["action"] == "READ"
    assert audit_logger.logs[0]["resource"] == "cases"
    assert audit_logger.logs[0]["user_id"] == 1

def test_prediction_audit(monkeypatch, audit_logger):
    mock_user = _mock_user()
    monkeypatch.setattr("app.api.deps.get_user_by_username", lambda db, username: mock_user)
    
    # Mock generating prediction successfully
    from app.services import prediction_service
    monkeypatch.setattr(prediction_service, "generate_prediction", lambda db, req, mock: {
        "case_id": req.case_id, 
        "risk": "HIGH", 
        "explanation": ["test explanation"],
        "time_window": "30d",
        "predictions": [{
            "rank": 1,
            "atm_id": "ATM-1",
            "probability": 0.9,
            "latitude": 0.0,
            "longitude": 0.0,
            "risk": "HIGH"
        }]
    })
    
    token = create_access_token({"sub": "admin", "role": "Administrator"})
    res = client.post("/predict", json={"case_id": "C-123"}, headers=_auth_header(token))
    
    assert res.status_code == 200
    assert len(audit_logger.logs) == 1
    assert audit_logger.logs[0]["action"] == "PREDICT"
    assert audit_logger.logs[0]["status"] == "SUCCESS"
    assert "C-123" in audit_logger.logs[0]["resource"]

def test_rbac_denial_audit(monkeypatch, audit_logger):
    # Analyst trying to update an alert
    mock_user = _mock_user("analyst", RoleEnum.I4C_ANALYST)
    monkeypatch.setattr("app.api.deps.get_user_by_username", lambda db, username: mock_user)
    
    token = create_access_token({"sub": "analyst", "role": RoleEnum.I4C_ANALYST.value})
    res = client.patch("/alerts/1/status", json={"status": "RESOLVED"}, headers=_auth_header(token))
    
    assert res.status_code == 403
    assert len(audit_logger.logs) == 1
    assert audit_logger.logs[0]["action"] == "ACCESS_DENIED"
    assert audit_logger.logs[0]["status"] == "DENIED"

def test_audit_retrieval_admin(monkeypatch):
    mock_user = _mock_user("admin", RoleEnum.ADMIN)
    monkeypatch.setattr("app.api.deps.get_user_by_username", lambda db, username: mock_user)
    
    from app.crud import crud_audit
    monkeypatch.setattr(crud_audit, "get_audit_logs", lambda db, skip, limit: [])
    
    token = create_access_token({"sub": "admin", "role": RoleEnum.ADMIN.value})
    res = client.get("/audit", headers=_auth_header(token))
    assert res.status_code == 200

def test_audit_retrieval_investigator_denied(monkeypatch, audit_logger):
    mock_user = _mock_user("investigator", RoleEnum.LEA_INVESTIGATOR)
    monkeypatch.setattr("app.api.deps.get_user_by_username", lambda db, username: mock_user)
    
    token = create_access_token({"sub": "investigator", "role": RoleEnum.LEA_INVESTIGATOR.value})
    res = client.get("/audit", headers=_auth_header(token))
    assert res.status_code == 403
    
    assert len(audit_logger.logs) == 1
    assert audit_logger.logs[0]["action"] == "ACCESS_DENIED"
