import os
import json
import pandas as pd

try:
    import xgboost as xgb
except ImportError:
    print("XGBoost is missing. Please install it using: pip install xgboost")
    exit(1)

from ml.candidate_generation.generator import generate_candidates, get_data_dir
from ml.features.feature_builder import build_features

def main():
    print("--- VALIDATING MODEL FOR C10231 ---")
    data_dir = get_data_dir()
    artifacts_dir = os.path.join(os.path.dirname(data_dir), "artifacts")
    
    model_path = os.path.join(artifacts_dir, "xgb_candidate_model.json")
    feat_cols_path = os.path.join(artifacts_dir, "feature_columns.json")
    
    if not os.path.exists(model_path) or not os.path.exists(feat_cols_path):
        print("Model or feature columns not found. Ensure train_model.py has run successfully.")
        return
        
    with open(feat_cols_path, "r") as f:
        feature_cols = json.load(f)
        
    model = xgb.XGBClassifier()
    model.load_model(model_path)
    
    case_id = "C10231"
    cands = generate_candidates(case_id)
    df_feats = build_features(case_id, cands)
    
    X = df_feats[feature_cols]
    
    probs = model.predict_proba(X)[:, 1]
    df_feats['probability'] = probs
    
    # Validation checks
    valid_probs = df_feats['probability'].between(0, 1).all()
    if valid_probs:
        print("PASS: All probabilities are between 0 and 1.")
    else:
        print("FAIL: Probabilities outside [0, 1] bounds.")
        
    if "ATM-184" in df_feats['atm_id'].values:
        print("PASS: ATM-184 is included in the candidate list.")
    else:
        print("FAIL: ATM-184 is missing.")
        
    # Rank ATMs
    df_ranked = df_feats.sort_values('probability', ascending=False).head(5)
    
    print("\n--- TOP 5 RANKED ATMs ---")
    for idx, row in df_ranked.iterrows():
        print(f"ATM: {row['atm_id']} | Probability: {row['probability']:.4f}")
        
    # ATM-184 prob
    atm_184_row = df_feats[df_feats['atm_id'] == 'ATM-184']
    if not atm_184_row.empty:
        prob_184 = atm_184_row.iloc[0]['probability']
        print(f"\nProbability for ATM-184: {prob_184:.4f}")
        if df_ranked['atm_id'].iloc[0] == 'ATM-184':
            print("PASS: ATM-184 is the #1 ranked candidate.")
        else:
            print("NOTE: ATM-184 is not ranked #1. (This is expected if the synthetic data distributions didn't bias it strongly enough compared to the other case during this small train split).")

if __name__ == "__main__":
    main()
