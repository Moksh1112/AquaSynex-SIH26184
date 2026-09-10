import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.crud import crud_case
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

# --- Tests that can run WITHOUT a live database (Mocked) ---

def test_get_cases_mocked(monkeypatch):
    """Test retrieving cases with mocked repository."""
    _mock_auth(monkeypatch)
    
    class MockCase:
        def __init__(self, id, case_id, description, status, reported_at):
            self.id = id
            self.case_id = case_id
            self.description = description
            self.status = status
            self.reported_at = reported_at

    mock_cases = [
        MockCase(1, "C-2026-9081", "Victim reported fraud", "OPEN", datetime.utcnow())
    ]
    
    def mock_get_cases(db, skip=0, limit=100):
        return mock_cases
    
    monkeypatch.setattr(crud_case, "get_cases", mock_get_cases)
    
    response = client.get("/cases", headers=_auth_header())
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["case_id"] == "C-2026-9081"
    assert data[0]["status"] == "OPEN"

def test_get_case_by_id_mocked(monkeypatch):
    """Test retrieving a specific case with mocked repository."""
    _mock_auth(monkeypatch)
    
    class MockCase:
        def __init__(self, id, case_id, description, status, reported_at):
            self.id = id
            self.case_id = case_id
            self.description = description
            self.status = status
            self.reported_at = reported_at

    mock_case = MockCase(1, "C-2026-9081", "Victim reported fraud", "OPEN", datetime.utcnow())

    def mock_get_case(db, case_id):
        if case_id == "C-2026-9081":
            return mock_case
        return None
    
    monkeypatch.setattr(crud_case, "get_case_by_case_id", mock_get_case)
    
    # Valid case
    response = client.get("/cases/C-2026-9081", headers=_auth_header())
    assert response.status_code == 200
    assert response.json()["case_id"] == "C-2026-9081"

    # Nonexistent case
    response_not_found = client.get("/cases/UNKNOWN-CASE", headers=_auth_header())
    assert response_not_found.status_code == 404
    assert response_not_found.json()["detail"] == "Case not found"


# --- Tests that REQUIRE PostgreSQL/PostGIS (Blocked) ---
from tests.db_utils import require_postgres

@require_postgres
def test_get_cases_integration(monkeypatch):
    """Integration test: actual database read."""
    _mock_auth(monkeypatch)
    res = client.get("/cases", headers=_auth_header())
    assert res.status_code == 200
    assert isinstance(res.json(), list)

@require_postgres
def test_get_case_by_id_integration(monkeypatch):
    """Integration test: actual database read for a specific case."""
    _mock_auth(monkeypatch)
    res = client.get("/cases", headers=_auth_header())
    assert res.status_code == 200
    cases = res.json()
    if cases:
        case_id = cases[0]["case_id"]
        res_single = client.get(f"/cases/{case_id}", headers=_auth_header())
        assert res_single.status_code == 200
        assert res_single.json()["case_id"] == case_id
