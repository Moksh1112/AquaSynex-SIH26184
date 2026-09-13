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
    if not cands:
        print("No candidates generated. Check data.")
        return
        
    df_feats = build_features(case_id, cands)
    if df_feats.empty:
        print("Feature extraction failed.")
        return
        
    from ml.prediction.predictor import predict_candidates
    df_feats = predict_candidates(model, df_feats)
    
    valid_probs = df_feats['probability'].between(0, 1).all()
    if valid_probs:
        print("PASS: All probabilities are between 0 and 1.")
    else:
        print("FAIL: Probabilities outside [0, 1] bounds.")
        
    if "ATM-0184" in df_feats['atm_id'].values:
        print("PASS: ATM-0184 is included in the candidate list.")
    else:
        print("FAIL: ATM-0184 is missing.")
        
    from ml.prediction.ranking import rank_candidates
    ranked_list = rank_candidates(df_feats)
    df_ranked = pd.DataFrame(ranked_list)
    
    top5 = df_ranked.head(5)
    print("\n--- TOP 5 RANKED ATMs ---")
    for idx, row in top5.iterrows():
        print(f"Rank {row['rank']}: {row['atm_id']} | Probability: {row['probability']:.4f}")
        
    atm_184_row = df_ranked[df_ranked['atm_id'] == 'ATM-0184']
    if not atm_184_row.empty:
        r = atm_184_row.iloc[0]
        print(f"\nTarget ATM-0184 is ranked #{r['rank']} with probability {r['probability']:.4f}")
        if r['rank'] <= 5:
            print("PASS: ATM-0184 is in the Top-5.")
        else:
            print("NOTE: ATM-0184 is outside the Top-5.")
    
    print("\n--- STAGES 3 & 4: TIME-WINDOW & EXPLANATION ---")
    from ml.prediction.time_window import predict_time_window
    window = predict_time_window(case_id)
    print(f"Predicted Time Window for {case_id}: {window}")
    
    window_missing = predict_time_window("UNKNOWN_CASE_999")
    print(f"Predicted Time Window for UNKNOWN_CASE_999: {window_missing}")
    
    from ml.explainability.shap_explainer import explain_prediction
    explanations = explain_prediction(df_ranked.head(5).to_dict('records'))
    print("\nExplanation for Top Candidate:")
    for exp in explanations:
        print(f" - {exp}")
    
    print("\nRELIABILITY STATEMENT:")
    print("This model is trained on synthetic data for prototype validation and is not production-ready. Real deployment requires real historical labeled data, calibration, monitoring, and retraining.")

if __name__ == "__main__":
    main()
