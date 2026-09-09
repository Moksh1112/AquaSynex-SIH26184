from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_predict_mock():
    response = client.post("/predict", json={"case_id": "C10231"})
    assert response.status_code == 200
    assert response.json()["case_id"] == "C10231"
