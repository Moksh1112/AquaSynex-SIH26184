import os
import json
import pandas as pd
import shap
import xgboost as xgb
import numpy as np

def get_artifacts_dir() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ml_dir = os.path.dirname(current_dir)
    return os.path.join(ml_dir, "artifacts")

def explain_prediction(prediction_data):
    """
    Generate SHAP explanations based on the candidate predictions using the real model.
    """
    if not prediction_data:
        return ["No prediction data available for explanation."]
        
    if isinstance(prediction_data, list):
        df = pd.DataFrame(prediction_data)
    else:
        df = prediction_data.copy()
        
    if df.empty:
        return ["No candidates available to generate explanation."]

    artifacts_dir = get_artifacts_dir()
    model_path = os.path.join(artifacts_dir, "xgb_candidate_model.json")
    feat_cols_path = os.path.join(artifacts_dir, "feature_columns.json")
    
    if not os.path.exists(model_path) or not os.path.exists(feat_cols_path):
        return ["Artifacts missing, unable to generate SHAP explanations."]

    try:
        model = xgb.XGBClassifier()
        model.load_model(model_path)
        
        with open(feat_cols_path, "r") as f:
            feature_cols = json.load(f)
            
        # Ensure columns
        for col in feature_cols:
            if col not in df.columns:
                df[col] = 0.0
                
        X = df[feature_cols]
        
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
        
        # If binary classification, shap_values might be a list of arrays (one for each class)
        # or a single array (for the positive class). XGBoost usually returns a single array for binary.
        if isinstance(shap_values, list):
            shap_vals_target = shap_values[1]
        else:
            shap_vals_target = shap_values
            
        explanations = []
        
        top_cand = df.iloc[0]
        atm_id = top_cand.get('atm_id', 'Unknown ATM')
        prob = top_cand.get('probability', 0.0)
        risk_str = "high risk" if prob > 0.5 else "predicted"
        explanations.append(f"Top candidate ({atm_id}) has a {risk_str} probability of {prob*100:.1f}%.")
        
        # Top 3 features pushing the prediction higher for the top candidate
        top_cand_shap = shap_vals_target[0]
        # Sort indices by shap value descending
        top_indices = np.argsort(top_cand_shap)[::-1][:3]
        
        explanations.append("Top factors driving this risk:")
        for idx in top_indices:
            feat_name = feature_cols[idx]
            feat_val = X.iloc[0, idx]
            shap_val = top_cand_shap[idx]
            if shap_val > 0.01:
                friendly_name = feat_name.replace('_', ' ').title()
                explanations.append(f"- {friendly_name} (Value: {feat_val:.2f})")
                
        if len(explanations) == 2:
            explanations.append("- Historical behavior patterns")
            
        return explanations
    except Exception as e:
        return [f"Error generating explanation: {e}"]
