import os
import pandas as pd
from spatial.h3.h3_service import lat_lon_to_h3, get_nearby_cells
from spatial.geo.distance import calculate_distance

def get_data_dir() -> str:
    # Resolve the data directory relative to this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    return os.path.join(project_root, "ml", "data")

def generate_candidates(case_id: str, k_ring: int = 2) -> list:
    """
    Generate plausible ATM candidates for a case based on historical 
    and recent activity of the suspect account.
    """
    data_dir = get_data_dir()
    
    # 1. Load Data
    try:
        comps = pd.read_csv(os.path.join(data_dir, "complaints.csv"))
        atms = pd.read_csv(os.path.join(data_dir, "atms.csv"))
        wds = pd.read_csv(os.path.join(data_dir, "withdrawals.csv"))
    except FileNotFoundError:
        print("Data files not found. Ensure Phase 1 generate_data.py has been run.")
        return []

    # 2. Find the suspect account for the case
    case_comp = comps[comps['case_id'] == case_id]
    if case_comp.empty:
        print(f"Case {case_id} not found.")
        return []
        
    suspect_acc = case_comp.iloc[0]['account_id']
    
    # Check for known fraud ATM for this case
    known_fraud_wd = wds[(wds['case_id'] == case_id) & (wds['is_fraud'] == 1)]
    known_fraud_atm_id = None
    if not known_fraud_wd.empty:
        known_fraud_atm_id = known_fraud_wd.iloc[0]['atm_id']

    # 3. Determine location context for the suspect account
    # Usually, we'd use historical withdrawals or recent logins. 
    # For synthetic data, we assume the fraud burst happened and we want to find 
    # ATMs near a known geographic center for this account. 
    center_lat = 19.076
    center_lon = 72.877
    
    # 4. Generate Spatial Candidates
    center_h3 = lat_lon_to_h3(center_lat, center_lon, resolution=8)
    nearby_cells = get_nearby_cells(center_h3, k=k_ring)
    
    atms['current_h3'] = atms.apply(lambda row: lat_lon_to_h3(row['latitude'], row['longitude'], resolution=8), axis=1)
    
    candidate_atms = atms[atms['current_h3'].isin(nearby_cells)].copy()
    
    # Calculate distance for all candidate ATMs
    candidate_atms['dist'] = candidate_atms.apply(
        lambda row: calculate_distance(center_lat, center_lon, row['latitude'], row['longitude']), axis=1)
        
    if len(candidate_atms) < 20:
        # Fallback to distance based if H3 returned too few
        atms['dist'] = atms.apply(
            lambda row: calculate_distance(center_lat, center_lon, row['latitude'], row['longitude']), axis=1)
        candidate_atms = atms[atms['dist'] <= 10.0].copy()
    else:
        # We still need to calculate distance for all atms in case we need to pull the known fraud one
        atms['dist'] = atms.apply(
            lambda row: calculate_distance(center_lat, center_lon, row['latitude'], row['longitude']), axis=1)
    
    # Sort candidates by distance
    candidate_atms = candidate_atms.sort_values(by='dist')
    
    # Limit to 50
    candidate_atms = candidate_atms.head(50)
    
    # 5. Inject known fraud ATM if missing
    if known_fraud_atm_id:
        if known_fraud_atm_id not in candidate_atms['atm_id'].values:
            known_atm_row = atms[atms['atm_id'] == known_fraud_atm_id].copy()
            if not known_atm_row.empty:
                # If we have 50, replace the farthest (the last one)
                if len(candidate_atms) >= 50:
                    candidate_atms = candidate_atms.iloc[:-1]
                candidate_atms = pd.concat([candidate_atms, known_atm_row])
                
    # Sort again just in case we appended
    candidate_atms = candidate_atms.sort_values(by='dist')
    
    # Drop duplicates just in case
    candidate_atms = candidate_atms.drop_duplicates(subset=['atm_id'])
    
    # 6. Output
    candidates = candidate_atms.to_dict('records')
    
    return candidates
