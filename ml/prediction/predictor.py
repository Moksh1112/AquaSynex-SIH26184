import os
import json
import pandas as pd

def get_artifacts_dir() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ml_dir = os.path.dirname(current_dir)
    return os.path.join(ml_dir, "artifacts")

def predict_candidates(model, candidates):
    """
    Predict fraud probability for a set of candidate ATMs.
    
    :param model: The trained ML model.
    :param candidates: A pandas DataFrame or list of dicts containing candidate features and metadata.
    :return: A pandas DataFrame with the predicted 'probability' column.
    """
    if isinstance(candidates, list):
        df = pd.DataFrame(candidates)
    else:
        df = candidates.copy()
        
    if df.empty:
        return df
        
    artifacts_dir = get_artifacts_dir()
    feat_cols_path = os.path.join(artifacts_dir, "feature_columns.json")
    
    if not os.path.exists(feat_cols_path):
        raise FileNotFoundError(f"Feature columns JSON not found at {feat_cols_path}. Train the model first.")
        
    with open(feat_cols_path, "r") as f:
        feature_cols = json.load(f)
        
    # Ensure all required feature columns are present safely
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0.0
            
    X = df[feature_cols]
    
    # Generate probabilities
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)
        if probs.ndim == 2:
            probs = probs[:, 1]
    else:
        probs = model.predict(X)
        
    df['probability'] = probs
    return df
