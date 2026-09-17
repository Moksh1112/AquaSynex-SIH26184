import os
import pandas as pd
from ml.candidate_generation.generator import generate_candidates_csv
from ml.features.feature_builder import get_data_dir

def run_diagnostics():
    data_dir = get_data_dir()
    comps = pd.read_csv(os.path.join(data_dir, "complaints.csv"), dtype={'case_id': str})
    wds = pd.read_csv(os.path.join(data_dir, "withdrawals.csv"), dtype={'case_id': str})
    atms = pd.read_csv(os.path.join(data_dir, "atms.csv"))
    
    fraud_wds = wds[wds['is_fraud'] == 1]
    
    total_cases = 0
    total_candidates = 0
    total_positives = 0
    total_negatives = 0
    cases_with_zero_positives = 0
    cases_with_multiple_positives = 0
    duplicate_candidate_atms = 0
    appended_count = 0
    
    print("Running Candidate Label Diagnostics...")
    
    valid_cases = fraud_wds['case_id'].unique()
    
    # Analyze all valid cases to get true metrics
    for case_id in valid_cases:
        total_cases += 1
        known_fraud_wds = wds[(wds['case_id'] == case_id) & (wds['is_fraud'] == 1)]
        known_atms = known_fraud_wds['atm_id'].unique()
        
        cands = generate_candidates_csv(case_id, k_ring=2)
        if not cands:
            cases_with_zero_positives += 1
            continue
            
        cand_df = pd.DataFrame(cands)
        total_candidates += len(cand_df)
        
        # Check duplicates
        dupes = len(cand_df) - cand_df['atm_id'].nunique()
        duplicate_candidate_atms += dupes
        
        # Count positives
        positives = cand_df[cand_df['atm_id'].isin(known_atms)]
        num_pos = len(positives)
        total_positives += num_pos
        total_negatives += (len(cand_df) - num_pos)
        
        if num_pos == 0:
            cases_with_zero_positives += 1
        elif num_pos > 1:
            cases_with_multiple_positives += 1
            
        # Detect if it was artificially appended.
        # In generator.py, known ATM distance is kept as 0.0 if appended manually in Postgres.
        # In CSV, it's appended from known_atm_row.
        # To strictly check if it's appended, we could see if the distance is greater than the 49th ATM but it's ranked last,
        # or just look at generator logic. generator.py does candidate_atms = pd.concat([candidate_atms, known_atm_row])
        # and then sorts by dist. So it's not distinguishable just by order unless we re-run the distance filter.
        # We'll just infer it manually.
        
    print(f"Total cases evaluated: {total_cases}")
    print(f"Total candidates generated: {total_candidates}")
    print(f"Total positives: {total_positives}")
    print(f"Total negatives: {total_negatives}")
    ratio = total_positives / total_negatives if total_negatives > 0 else 0
    print(f"Positive-to-negative ratio: 1 : {1/ratio:.2f}" if ratio > 0 else "Ratio: N/A")
    print(f"Cases with zero positives: {cases_with_zero_positives}")
    print(f"Cases with multiple positives: {cases_with_multiple_positives}")
    print(f"Duplicate candidate ATM IDs: {duplicate_candidate_atms}")
    
if __name__ == "__main__":
    run_diagnostics()
