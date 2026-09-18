import os
import logging
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score, log_loss

from ml.features.feature_builder import get_data_dir, load_datasets, build_features_for_case
from ml.candidate_generation.generator import generate_candidates_csv
from ml.training.evaluate import evaluate_ranking

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_model():
    logger.info("Loading datasets...")
    comps, atms, txs, wds = load_datasets()

    fraud_cases = wds[wds['is_fraud'] == 1]['case_id'].unique()
    valid_cases = comps[comps['case_id'].isin(fraud_cases)]['case_id'].tolist()

    sample_cases = valid_cases[:50]
    all_features = []

    logger.info(f"Extracting features for {len(sample_cases)} cases...")
    for case_id in sample_cases:
        cands = generate_candidates_csv(case_id, k_ring=2)
        if not cands:
            continue

        df_feats = build_features_for_case(case_id, cands, comps, atms, txs, wds)
        if not df_feats.empty:
            all_features.append(df_feats)

    if not all_features:
        logger.error("No features extracted. Cannot train.")
        return

    df_train = pd.concat(all_features, ignore_index=True)

    if 'label' not in df_train.columns or 'case_id' not in df_train.columns:
        logger.error("Missing label or case_id column.")
        return

    # STEP 4: GroupShuffleSplit to prevent data leakage
    groups = df_train['case_id']
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    
    train_idx, test_idx = next(gss.split(df_train, groups=groups))
    
    df_train_set = df_train.iloc[train_idx]
    df_test_set = df_train.iloc[test_idx]
    
    logger.info(f"Train cases: {df_train_set['case_id'].nunique()}, Test cases: {df_test_set['case_id'].nunique()}")
    logger.info(f"Train candidates: {len(df_train_set)}, Test candidates: {len(df_test_set)}")

    y_train = df_train_set['label']
    y_test = df_test_set['label']

    drop_cols = ['case_id', 'atm_id', 'label']
    X_train = df_train_set.drop(columns=[col for col in drop_cols if col in df_train_set.columns])
    X_test = df_test_set.drop(columns=[col for col in drop_cols if col in df_test_set.columns])

    # STEP 5: Calculate actual ratio for scale_pos_weight
    neg_count = sum(y_train == 0)
    pos_count = sum(y_train == 1)
    spw = neg_count / pos_count if pos_count > 0 else 1.0
    logger.info(f"Class imbalance handling: scale_pos_weight = {spw:.2f}")

    logger.info(f"Training XGBoost (Revised) on {len(X_train)} samples...")
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
        use_label_encoder=False,
        eval_metric='logloss',
        scale_pos_weight=spw
    )

    model.fit(X_train, y_train)

    logger.info("Evaluating model...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_prob)) if len(set(y_test)) > 1 else 0.0,
        "log_loss": float(log_loss(y_test, y_prob)) if len(set(y_test)) > 1 else 0.0
    }

    # STEP 6: Custom Ranking Evaluation
    df_test_set_copy = df_test_set.copy()
    df_test_set_copy['probability'] = y_prob
    ranking_metrics = evaluate_ranking(df_test_set_copy)
    metrics.update(ranking_metrics)

    logger.info(f"Metrics: {metrics}")
    logger.info(f"Confusion Matrix:\n{confusion_matrix(y_test, y_pred)}")

    data_dir = get_data_dir()
    artifacts_dir = os.path.join(os.path.dirname(data_dir), "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    model_path = os.path.join(artifacts_dir, "xgb_candidate_model.json")
    model.save_model(model_path)
    logger.info(f"Revised model saved to {model_path}")

    # Save feature columns for SHAP
    feature_cols_path = os.path.join(artifacts_dir, "feature_columns.json")
    with open(feature_cols_path, "w") as f:
        import json
        json.dump(list(X_train.columns), f, indent=2)
    logger.info(f"Feature columns saved to {feature_cols_path}")

    metrics_path = os.path.join(artifacts_dir, "training_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

if __name__ == "__main__":
    train_model()
