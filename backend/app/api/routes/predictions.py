from fastapi import APIRouter
from app.schemas.prediction import PredictRequest, PredictResponse
from app.services.prediction_service import get_mock_prediction

router = APIRouter()

@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    """
    Returns a prediction for the given case_id.
    Currently returns a mock prediction complying with the API contract.
    """
    return get_mock_prediction(request.case_id)
