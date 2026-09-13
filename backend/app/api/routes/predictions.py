from fastapi import APIRouter
from app.schemas.prediction import PredictRequest, PredictResponse
from app.services.prediction_service import get_prediction

router = APIRouter()

@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    """
    Returns a prediction for the given case_id.
    """
    return get_prediction(request.case_id)
