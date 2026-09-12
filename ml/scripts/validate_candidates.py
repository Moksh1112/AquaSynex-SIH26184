import os
import pandas as pd
from ml.candidate_generation.generator import generate_candidates, get_data_dir

def test_candidate_generation():
    print("--- VALIDATING CANDIDATE GENERATION ---")
    case_id = "C10231"
    
    data_dir = get_data_dir()
    wds = pd.read_csv(os.path.join(data_dir, "withdrawals.csv"))
    known_fraud_wd = wds[(wds['case_id'] == case_id) & (wds['is_fraud'] == 1)]
    known_fraud_atm_id = known_fraud_wd.iloc[0]['atm_id'] if not known_fraud_wd.empty else None
    
    candidates = generate_candidates(case_id)
    
    print(f"\nCase ID: {case_id}")
    print(f"Total candidates generated: {len(candidates)}")
    print(f"Known Fraud ATM for this case: {known_fraud_atm_id}")
    
    # Check bounds
    if len(candidates) >= 20 and len(candidates) <= 50:
        print("PASS: Candidate count is within 20-50 range.")
    else:
        print(f"FAIL: Candidate count {len(candidates)} is out of bounds (expected 20-50).")
        
    # Check known fraud ATM
    atm_ids = [c['atm_id'] for c in candidates]
    if known_fraud_atm_id:
        if known_fraud_atm_id in atm_ids:
            print(f"PASS: {known_fraud_atm_id} (Fraud Cashout ATM) is present in candidates.")
        else:
            print(f"FAIL: {known_fraud_atm_id} is missing from candidates.")
    
    # Check duplicates
    if len(atm_ids) == len(set(atm_ids)):
        print("PASS: No duplicate ATM IDs.")
    else:
        print("FAIL: Duplicate ATM IDs found.")
        
    # Check coordinates
    valid_coords = True
    for c in candidates:
        lat, lon = c.get('latitude'), c.get('longitude')
        if lat is None or lon is None or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            valid_coords = False
            print(f"FAIL: Invalid coordinates for ATM {c.get('atm_id')}: lat={lat}, lon={lon}")
            break
            
    if valid_coords:
        print("PASS: All candidates have valid coordinates.")
        
    print("\nSample Candidates:")
    for c in candidates[:5]:
        print(f" - {c['atm_id']} at {c['latitude']}, {c['longitude']} (Dist: {c.get('dist', 'N/A')} km)")

if __name__ == "__main__":
    test_candidate_generation()
