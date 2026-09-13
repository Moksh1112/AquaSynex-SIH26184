from app.schemas.prediction import PredictResponse

import os
import pandas as pd
import xgboost as xgb

from app.schemas.prediction import PredictResponse, PredictionItem
from ml.candidate_generation.generator import generate_candidates, get_data_dir
from ml.features.feature_builder import build_features
from ml.prediction.predictor import predict_candidates
from ml.prediction.ranking import rank_candidates
from ml.prediction.time_window import predict_time_window
from ml.explainability.shap_explainer import explain_prediction

def get_prediction(case_id: str) -> dict:
    data_dir = get_data_dir()
    artifacts_dir = os.path.join(os.path.dirname(data_dir), "artifacts")
    model_path = os.path.join(artifacts_dir, "xgb_candidate_model.json")
    
    time_window = predict_time_window(case_id)
    
    fallback_response = {
        "case_id": case_id,
        "risk": "UNKNOWN",
        "predicted_time_window": time_window,
        "ranked_candidates": [],
        "explanations": ["Insufficient data to generate prediction."],
        "reliability_statement": "This model is trained on synthetic data for prototype validation and is not production-ready."
    }
    
    if not os.path.exists(model_path):
        return fallback_response
        
    model = xgb.XGBClassifier()
    try:
        model.load_model(model_path)
    except Exception:
        return fallback_response
        
    cands = generate_candidates(case_id)
    if not cands:
        return fallback_response
        
    df_feats = build_features(case_id, cands)
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
    for cand in ranked_list[:10]:
        atm_id = str(cand['atm_id'])
        prob = float(cand['probability'])
        risk_label = "HIGH" if prob > 0.5 else "LOW"
        lat, lon = coords_map.get(atm_id, (0.0, 0.0))
        
        predictions.append({
            "rank": int(cand['rank']),
            "atm_id": atm_id,
            "probability": prob,
            "latitude": float(lat),
            "longitude": float(lon),
            "risk": risk_label
        })
        
    overall_risk = "HIGH" if predictions and predictions[0]['risk'] == "HIGH" else "LOW"
    
    return {
        "case_id": case_id,
        "risk": overall_risk,
        "predicted_time_window": time_window,
        "ranked_candidates": predictions,
        "explanations": explanations,
        "reliability_statement": "This model is trained on synthetic data for prototype validation and is not production-ready."
    }
