from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_predict_valid_case():
    response = client.post("/predict", json={"case_id": "C10231"})
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "C10231"
    assert "predicted_time_window" in data
    assert "ranked_candidates" in data
    assert "explanations" in data
    assert "reliability_statement" in data
    
    if data["ranked_candidates"]:
        top = data["ranked_candidates"][0]
        assert "rank" in top
        assert "atm_id" in top
        assert top["atm_id"] == "ATM-0184" # Target ATM inclusion
        assert 0.0 <= top["probability"] <= 1.0 # Probabilities between 0 and 1
        
        # Test ranking is sorted correctly
        ranks = [c["rank"] for c in data["ranked_candidates"]]
        assert ranks == sorted(ranks)

def test_predict_unknown_case():
    response = client.post("/predict", json={"case_id": "UNKNOWN_999"})
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "UNKNOWN_999"
    assert data["predicted_time_window"] == "Insufficient historical data"
    assert len(data["ranked_candidates"]) == 0

