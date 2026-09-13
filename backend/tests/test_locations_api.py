import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api import deps
from app.models.atm import ATM

client = TestClient(app)

def test_get_locations_mocked(monkeypatch):
    """Test retrieving locations with mocked database."""
    
    def mock_get_db():
        class MockSession:
            def query(self, model):
                class QueryMock:
                    def all(self):
                        return [
                            ATM(atm_id="ATM-MUM-01", latitude=19.076, longitude=72.877, address="Mumbai"),
                            ATM(atm_id="ATM-MUM-02", latitude=19.081, longitude=72.882, address="Mumbai")
                        ]
                return QueryMock()
        return MockSession()
    
    app.dependency_overrides[deps.get_db] = mock_get_db
    
    response = client.get("/locations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["atm_id"] == "ATM-MUM-01"
    assert data[0]["latitude"] == 19.076
    
    app.dependency_overrides.pop(deps.get_db, None)

# --- Tests that REQUIRE PostgreSQL/PostGIS (Blocked) ---
from tests.db_utils import require_postgres

@require_postgres
def test_get_locations_integration():
    """Integration test: actual database read."""
    res = client.get("/locations")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
