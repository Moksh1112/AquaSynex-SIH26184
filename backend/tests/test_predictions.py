from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_predict_valid_case():
    response = client.post("/predict", json={"case_id": "C10231"})
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "C10231"
    assert "time_window" in data
    assert "predictions" in data
    assert "explanation" in data
    
    if data["predictions"]:
        top = data["predictions"][0]
        assert "rank" in top
        assert "atm_id" in top
        assert top["atm_id"] == "ATM-0184" # Target ATM inclusion
        assert 0.0 <= top["probability"] <= 1.0 # Probabilities between 0 and 1
        
        # Test ranking is sorted correctly
        ranks = [c["rank"] for c in data["predictions"]]
        assert ranks == sorted(ranks)

def test_predict_unknown_case():
    response = client.post("/predict", json={"case_id": "UNKNOWN_999"})
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "UNKNOWN_999"
    assert data["time_window"] == "Insufficient historical data"
    assert len(data["predictions"]) == 0

