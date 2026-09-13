import os
import json
import time
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import roc_auc_score, average_precision_score, precision_score, recall_score, f1_score, confusion_matrix

try:
    import xgboost as xgb
except ImportError:
    print("XGBoost is missing. Please install it using: pip install xgboost")
    exit(1)

from ml.candidate_generation.generator import generate_candidates_for_case, get_data_dir
from ml.features.feature_builder import build_features_for_case, load_datasets

def calculate_ranking_metrics(df_test):
    # Sort by probability descending
    df_test = df_test.sort_values(['case_id', 'probability'], ascending=[True, False])
    
    # Calculate ranks
    df_test['rank'] = df_test.groupby('case_id').cumcount() + 1
    
    # Filter to only the actual positive rows
    positives = df_test[df_test['label'] == 1]
    
    if positives.empty:
        return 0.0, 0.0, 0.0, 0.0
        
    # If a case has multiple positives, we take the rank of the *first* (highest ranked) positive
    first_pos_ranks = positives.groupby('case_id')['rank'].min()
    
    top1 = (first_pos_ranks <= 1).mean()
    top3 = (first_pos_ranks <= 3).mean()
    top5 = (first_pos_ranks <= 5).mean()
    mrr = (1.0 / first_pos_ranks).mean()
    
    return top1, top3, top5, mrr

def main():
    print("--- STAGE 4: LARGE-SCALE MODEL TRAINING ---")
    start_time = time.time()
    
    print("Loading datasets...")
    comps, atms, txs, wds = load_datasets()
    case_ids = comps['case_id'].unique()
    print(f"Found {len(case_ids)} cases for training.")
    
    all_features = []
    
    # Pre-compute current_h3 for atms to save time in loop
    from spatial.h3.h3_service import lat_lon_to_h3
    atms['current_h3'] = atms.apply(lambda row: lat_lon_to_h3(row['latitude'], row['longitude'], resolution=8), axis=1)
    
    print("Extracting features (this may take a moment)...")
    for idx, cid in enumerate(case_ids):
        if idx > 0 and idx % 500 == 0:
            print(f"  Processed {idx}/{len(case_ids)} cases...")
            
        cands = generate_candidates_for_case(cid, comps, atms, wds)
        if len(cands) > 0:
            df_feats = build_features_for_case(cid, cands, comps, atms, txs, wds)
            if not df_feats.empty:
                all_features.append(df_feats)
            
    if not all_features:
        print("No features generated.")
        return
        
    full_df = pd.concat(all_features, ignore_index=True)
    
    print(f"Feature extraction complete in {time.time() - start_time:.2f}s")
    
    total_cases = full_df['case_id'].nunique()
    total_rows = len(full_df)
    total_pos = full_df['label'].sum()
    total_neg = total_rows - total_pos
    pos_pct = (total_pos / total_rows) * 100
    pos_cases = full_df[full_df['label'] == 1]['case_id'].nunique()
    
    print("\n--- DATASET SUMMARY ---")
    print(f"Total Cases: {total_cases}")
    print(f"Total Candidate Rows: {total_rows}")
    print(f"Total Positive Labels: {total_pos}")
    print(f"Total Negative Labels: {total_neg}")
    print(f"Positive Percentage: {pos_pct:.2f}%")
    print(f"Cases with Positive Labels: {pos_cases}")
    
    drop_cols = ['case_id', 'atm_id', 'label']
    feature_cols = [c for c in full_df.columns if c not in drop_cols]
    
    print("\nSplitting train/test...")
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(full_df, groups=full_df['case_id']))
    
    train_df = full_df.iloc[train_idx]
    test_df = full_df.iloc[test_idx]
    
    X_train = train_df[feature_cols]
    y_train = train_df['label']
    X_test = test_df[feature_cols]
    y_test = test_df['label']
    
    print(f"Train cases: {train_df['case_id'].nunique()} | Train Pos: {y_train.sum()} | Train Neg: {len(y_train) - y_train.sum()}")
    print(f"Test cases: {test_df['case_id'].nunique()} | Test Pos: {y_test.sum()} | Test Neg: {len(y_test) - y_test.sum()}")
    
    pos_count = y_train.sum()
    neg_count = len(y_train) - pos_count
    scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0
    
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=2,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric='aucpr',
        early_stopping_rounds=30
    )
    
    print("\nTraining XGBClassifier...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=50
    )
    
    if y_test.sum() > 0:
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        # Test df with probas for ranking
        test_df_results = test_df.copy()
        test_df_results['probability'] = y_prob
        
        top1, top3, top5, mrr = calculate_ranking_metrics(test_df_results)
        
        print("\n--- EVALUATION METRICS ---")
        print(f"ROC-AUC: {roc_auc_score(y_test, y_prob):.4f}")
        print(f"PR-AUC: {average_precision_score(y_test, y_prob):.4f}")
        print(f"Precision: {precision_score(y_test, y_pred, zero_division=0):.4f}")
        print(f"Recall: {recall_score(y_test, y_pred, zero_division=0):.4f}")
        print(f"F1-Score: {f1_score(y_test, y_pred, zero_division=0):.4f}")
        print("Confusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        
        print("\n--- RANKING METRICS ---")
        print(f"Top-1 Accuracy: {top1:.4f}")
        print(f"Top-3 Accuracy: {top3:.4f}")
        print(f"Top-5 Accuracy: {top5:.4f}")
        print(f"Mean Reciprocal Rank (MRR): {mrr:.4f}")
        
    data_dir = get_data_dir()
    artifacts_dir = os.path.join(os.path.dirname(data_dir), "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)
    
    model_path = os.path.join(artifacts_dir, "xgb_candidate_model.json")
    model.save_model(model_path)
    
    feat_cols_path = os.path.join(artifacts_dir, "feature_columns.json")
    with open(feat_cols_path, "w") as f:
        json.dump(feature_cols, f)
        
    # Feature Importance
    importances = model.feature_importances_
    feat_imp = {col: float(imp) for col, imp in zip(feature_cols, importances)}
    feat_imp_path = os.path.join(artifacts_dir, "feature_importance.json")
    with open(feat_imp_path, "w") as f:
        json.dump(feat_imp, f, indent=4)
        
    print(f"\nArtifacts saved to: {artifacts_dir}")
    print("\nRELIABILITY STATEMENT:")
    print("This model is trained on synthetic data for prototype validation and is not production-ready. Real deployment requires real historical labeled data, calibration, monitoring, and retraining.")

if __name__ == "__main__":
    main()
