import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.alert import Alert
from app.schemas.alert import AlertStatusEnum
from app.core.security import create_access_token
from app.models.user import User, RoleEnum

client = TestClient(app)

def _auth_header():
    token = create_access_token(data={"sub": "admin", "role": RoleEnum.ADMIN.value})
    return {"Authorization": f"Bearer {token}"}

def _mock_auth(monkeypatch):
    mock_user = User(id=1, username="admin", email="a@b.com",
                     hashed_password="fakehash", role=RoleEnum.ADMIN)
    monkeypatch.setattr("app.api.deps.get_user_by_username", lambda db, username: mock_user)

def test_get_alerts(monkeypatch):
    _mock_auth(monkeypatch)
    
    def mock_get_alerts(db, skip, limit):
        return [Alert(id=1, case_id="C-1", priority="P1", status=AlertStatusEnum.OPEN)]
        
    from app.crud import crud_alert
    monkeypatch.setattr(crud_alert, "get_alerts", mock_get_alerts)
    
    response = client.get("/alerts", headers=_auth_header())
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["status"] == "OPEN"

def test_get_alert_by_id(monkeypatch):
    _mock_auth(monkeypatch)
    
    def mock_get_alert(db, alert_id):
        if alert_id == 1:
            return Alert(id=1, case_id="C-1", priority="P1", status=AlertStatusEnum.OPEN)
        return None
        
    from app.crud import crud_alert
    monkeypatch.setattr(crud_alert, "get_alert", mock_get_alert)
    
    res1 = client.get("/alerts/1", headers=_auth_header())
    assert res1.status_code == 200
    assert res1.json()["id"] == 1
    
    res2 = client.get("/alerts/99", headers=_auth_header())
    assert res2.status_code == 404

def test_patch_alert_status(monkeypatch):
    _mock_auth(monkeypatch)
    
    def mock_update(db, alert_id, status_in):
        if alert_id == 1:
            return Alert(id=1, case_id="C-1", priority="P1", status=status_in.status)
        return None
        
    from app.crud import crud_alert
    monkeypatch.setattr(crud_alert, "update_alert_status", mock_update)
    
    headers = _auth_header()
    
    res1 = client.patch("/alerts/1/status", json={"status": "IN_PROGRESS"}, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["status"] == "IN_PROGRESS"
    
    res2 = client.patch("/alerts/99/status", json={"status": "RESOLVED"}, headers=headers)
    assert res2.status_code == 404
    
    res3 = client.patch("/alerts/1/status", json={"status": "INVALID_STATUS"}, headers=headers)
    assert res3.status_code == 422 # Pydantic validation error
