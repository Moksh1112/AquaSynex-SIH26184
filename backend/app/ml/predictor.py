from abc import ABC, abstractmethod
from typing import List
from app.schemas.prediction import PredictResponse, PredictionItem

class Predictor(ABC):
    @abstractmethod
    def predict(self, case_id: str, context_data: dict) -> PredictResponse:
        pass

class MockPredictor(Predictor):
    def predict(self, case_id: str, context_data: dict) -> PredictResponse:
        # Generate synthetic deterministic mock data
        # We simulate that the model has identified ATM-184 and ATM-092
        predictions = [
            PredictionItem(
                rank=1,
                atm_id="ATM-MUM-01",
                probability=0.82,
                latitude=19.076,
                longitude=72.877,
                risk="HIGH"
            ),
            PredictionItem(
                rank=2,
                atm_id="ATM-MUM-02",
                probability=0.74,
                latitude=19.081,
                longitude=72.882,
                risk="HIGH"
            )
        ]
        
        explanation = [
            "High recent transaction velocity",
            "Similar historical cash-out behaviour"
        ]
        
        return PredictResponse(
            case_id=case_id,
            risk="HIGH",
            time_window="22:00-23:00",
            predictions=predictions,
            explanation=explanation
        )
