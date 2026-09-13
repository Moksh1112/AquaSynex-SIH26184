from app.schemas.prediction import PredictResponse

from app.schemas.prediction import PredictResponse
from app.ml.predictor import RealPredictor

predictor = RealPredictor()

def get_prediction(case_id: str) -> PredictResponse:
    """
    Generates a prediction using the RealPredictor.
    """
    return predictor.predict(case_id)
