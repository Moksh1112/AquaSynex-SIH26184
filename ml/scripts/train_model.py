import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import roc_auc_score, average_precision_score, precision_score, recall_score, f1_score, confusion_matrix

try:
    import xgboost as xgb
except ImportError:
    print("XGBoost is missing. Please install it using: pip install xgboost")
    exit(1)

from ml.candidate_generation.generator import generate_candidates, get_data_dir
from ml.features.feature_builder import build_features

def main():
    print("--- STAGE 4: MODEL TRAINING ---")
    data_dir = get_data_dir()
    
    try:
        comps = pd.read_csv(os.path.join(data_dir, "complaints.csv"))
    except FileNotFoundError:
        print("Data files not found.")
        return
        
    case_ids = comps['case_id'].unique()
    print(f"Found {len(case_ids)} cases for training.")
    
    all_features = []
    for cid in case_ids:
        cands = generate_candidates(cid)
        if len(cands) > 0:
            df_feats = build_features(cid, cands)
            all_features.append(df_feats)
            
    if not all_features:
        print("No features generated.")
        return
        
    full_df = pd.concat(all_features, ignore_index=True)
    
    print(f"Total dataset shape: {full_df.shape}")
    print(f"Total positive labels: {full_df['label'].sum()}")
    
    # Define columns to drop for modeling
    drop_cols = ['case_id', 'atm_id', 'label']
    feature_cols = [c for c in full_df.columns if c not in drop_cols]
    
    # Prevent data leakage: Split by case_id
    gss = GroupShuffleSplit(n_splits=1, test_size=0.5, random_state=42)
    
    # Since we only have 2 cases in the synthetic dataset, 50/50 split will put 1 case in train and 1 in test
    train_idx, test_idx = next(gss.split(full_df, groups=full_df['case_id']))
    
    train_df = full_df.iloc[train_idx]
    test_df = full_df.iloc[test_idx]
    
    X_train = train_df[feature_cols]
    y_train = train_df['label']
    
    X_test = test_df[feature_cols]
    y_test = test_df['label']
    
    print(f"Train cases: {train_df['case_id'].nunique()}, Test cases: {test_df['case_id'].nunique()}")
    
    # Scale pos weight
    pos_count = y_train.sum()
    neg_count = len(y_train) - pos_count
    scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0
    
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric='logloss'
    )
    
    print("Training XGBClassifier...")
    model.fit(X_train, y_train)
    
    # Evaluate
    # If the test set has no positive labels (which can happen with few cases), evaluation metrics might complain
    if y_test.sum() > 0:
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        print("\n--- EVALUATION METRICS ---")
        print(f"ROC-AUC: {roc_auc_score(y_test, y_prob):.4f}")
        print(f"PR-AUC: {average_precision_score(y_test, y_prob):.4f}")
        print(f"Precision: {precision_score(y_test, y_pred, zero_division=0):.4f}")
        print(f"Recall: {recall_score(y_test, y_pred, zero_division=0):.4f}")
        print(f"F1-Score: {f1_score(y_test, y_pred, zero_division=0):.4f}")
        print("Confusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
    else:
        print("\nWarning: No positive labels in the test set. Skipping standard metric evaluation.")
        
    # Save artifacts
    artifacts_dir = os.path.join(os.path.dirname(data_dir), "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)
    
    model_path = os.path.join(artifacts_dir, "xgb_candidate_model.json")
    model.save_model(model_path)
    
    feat_cols_path = os.path.join(artifacts_dir, "feature_columns.json")
    with open(feat_cols_path, "w") as f:
        json.dump(feature_cols, f)
        
    print(f"\nModel saved to: {model_path}")
    print(f"Feature columns saved to: {feat_cols_path}")

if __name__ == "__main__":
    main()
