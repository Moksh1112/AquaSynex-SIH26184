import os
import pandas as pd
import xgboost as xgb
from abc import ABC, abstractmethod
from typing import List
from sqlalchemy.orm import Session
from app.schemas.prediction import PredictResponse, PredictionItem

# Import from ml module
from ml.candidate_generation.generator import generate_candidates, get_data_dir
from ml.features.feature_builder import build_features
from ml.prediction.predictor import predict_candidates
from ml.prediction.ranking import rank_candidates
from ml.prediction.time_window import predict_time_window
from ml.explainability.shap_explainer import explain_prediction

class Predictor(ABC):
    @abstractmethod
    def predict(self, db: Session, case_id: str, context_data: dict) -> PredictResponse:
        pass

class MockPredictor(Predictor):
    def predict(self, db: Session, case_id: str, context_data: dict) -> PredictResponse:
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

class RealPredictor(Predictor):
    def predict(self, db: Session, case_id: str, context_data: dict) -> PredictResponse:
        data_dir = get_data_dir()
        artifacts_dir = os.path.join(os.path.dirname(data_dir), "artifacts")
        model_path = os.path.join(artifacts_dir, "xgb_candidate_model.json")
        
        time_window = predict_time_window(case_id)
        
        fallback_response = PredictResponse(
            case_id=case_id,
            risk="UNKNOWN",
            time_window=time_window,
            predictions=[],
            explanation=["Insufficient data to generate prediction."]
        )
        
        if not os.path.exists(model_path):
            return fallback_response
            
        model = xgb.XGBClassifier()
        try:
            model.load_model(model_path)
        except Exception:
            return fallback_response
            
        cands = generate_candidates(db, case_id)
        if not cands:
            return fallback_response
            
        df_feats = build_features(db, case_id, cands)
        if df_feats.empty:
            return fallback_response
            
        df_pred = predict_candidates(model, df_feats)
        ranked_list = rank_candidates(df_pred)
        
        if not ranked_list:
            return fallback_response
            
        explanations = explain_prediction(ranked_list[:5])
        
        # Extract coordinates from original candidates
        coords_map = {c['atm_id']: (c.get('latitude', 0.0), c.get('longitude', 0.0)) for c in cands}
        
        predictions = []
        for cand in ranked_list[:5]:
            atm_id = str(cand['atm_id'])
            prob = float(cand['probability'])
            risk_label = "HIGH" if prob > 0.5 else "LOW"
            lat, lon = coords_map.get(atm_id, (0.0, 0.0))
            
            predictions.append(PredictionItem(
                rank=int(cand['rank']),
                atm_id=atm_id,
                probability=prob,
                latitude=float(lat),
                longitude=float(lon),
                risk=risk_label
            ))
            
        overall_risk = "HIGH" if predictions and predictions[0].risk == "HIGH" else "LOW"
        
        return PredictResponse(
            case_id=case_id,
            risk=overall_risk,
            time_window=time_window,
            predictions=predictions,
            explanation=explanations
        )
