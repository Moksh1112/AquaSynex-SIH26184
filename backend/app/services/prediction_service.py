from app.schemas.prediction import PredictResponse

def get_mock_prediction(case_id: str) -> dict:
    """
    Returns a mock prediction complying with the shared API contract.
    """
    return {
        "case_id": case_id,
        "risk": "HIGH",
        "time_window": "22:00-23:00",
        "predictions": [
            {
                "rank": 1,
                "atm_id": "ATM-184",
                "probability": 0.82,
                "latitude": 19.076,
                "longitude": 72.877,
                "risk": "HIGH"
            },
            {
                "rank": 2,
                "atm_id": "ATM-092",
                "probability": 0.74,
                "latitude": 19.081,
                "longitude": 72.882,
                "risk": "HIGH"
            }
        ],
        "explanation": [
            "High recent transaction velocity",
            "Similar historical cash-out behaviour",
            "High-risk connected account",
            "Short transfer-to-withdrawal interval"
        ]
    }
