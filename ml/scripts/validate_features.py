import pandas as pd
from ml.candidate_generation.generator import generate_candidates_csv
from ml.features.feature_builder import build_features_for_case, load_datasets

def test_features():
    print("--- VALIDATING FEATURE ENGINEERING ---")
    case_id = "C10231"
    
    print(f"Generating candidates for {case_id}...")
    candidates = generate_candidates_csv(case_id)
    
    print(f"Building features for {len(candidates)} candidates...")
    comps, atms, txs, wds = load_datasets()
    df = build_features_for_case(case_id, candidates, comps, atms, txs, wds)
    
    print("\n--- RESULTS ---")
    print(f"Shape: {df.shape}")
    
    # Confirm one row per candidate
    if len(df) == len(candidates):
        print("PASS: One row per candidate ATM.")
    else:
        print("FAIL: Row count mismatch.")
        
    # Confirm no duplicates
    if len(df) == len(df.drop_duplicates(subset=['case_id', 'atm_id'])):
        print("PASS: No duplicate case_id + atm_id pairs.")
    else:
        print("FAIL: Duplicates found.")
        
    # Confirm no NaNs
    if not df.isnull().values.any():
        print("PASS: No NaN values found.")
    else:
        print("FAIL: NaNs found.")
        
    # Confirm no infinites
    # We must select only numeric columns to test for infinity
    numeric_df = df.select_dtypes(include=['number'])
    import numpy as np
    if not np.isinf(numeric_df).values.any():
        print("PASS: No infinite values found.")
    else:
        print("FAIL: Infinite values found.")
        
    print("\n--- COLUMNS ---")
    print(df.columns.tolist())
    
    print("\n--- SAMPLE FRAUD ROW ---")
    fraud_rows = df[df['label'] == 1]
    if not fraud_rows.empty:
        print(fraud_rows.iloc[0].to_dict())
    else:
        print("FAIL: No fraud label (1) found in features.")

if __name__ == "__main__":
    test_features()
