import os
import pandas as pd
from spatial.h3.h3_service import lat_lon_to_h3, get_nearby_cells
from spatial.geo.distance import calculate_distance

def get_data_dir() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    return os.path.join(project_root, "ml", "data")

def generate_candidates_for_case(case_id: str, comps: pd.DataFrame, atms: pd.DataFrame, wds: pd.DataFrame, k_ring: int = 2) -> list:
    case_comp = comps[comps['case_id'] == case_id]
    if case_comp.empty:
        return []
        
    suspect_acc = case_comp.iloc[0]['account_id']
    
    known_fraud_wd = wds[(wds['case_id'] == case_id) & (wds['is_fraud'] == 1)]
    known_fraud_atm_id = None
    if not known_fraud_wd.empty:
        known_fraud_atm_id = known_fraud_wd.iloc[0]['atm_id']

    center_lat = 19.076
    center_lon = 72.877
    
    center_h3 = lat_lon_to_h3(center_lat, center_lon, resolution=8)
    nearby_cells = get_nearby_cells(center_h3, k=k_ring)
    
    # We assume 'current_h3' is already computed on atms for bulk operations
    if 'current_h3' not in atms.columns:
        atms['current_h3'] = atms.apply(lambda row: lat_lon_to_h3(row['latitude'], row['longitude'], resolution=8), axis=1)
    
    candidate_atms = atms[atms['current_h3'].isin(nearby_cells)].copy()
    
    candidate_atms['dist'] = candidate_atms.apply(
        lambda row: calculate_distance(center_lat, center_lon, row['latitude'], row['longitude']), axis=1)
        
    if len(candidate_atms) < 20:
        if 'dist' not in atms.columns:
            atms['dist'] = atms.apply(
                lambda row: calculate_distance(center_lat, center_lon, row['latitude'], row['longitude']), axis=1)
        candidate_atms = atms[atms['dist'] <= 10.0].copy()
    else:
        if 'dist' not in atms.columns:
             atms['dist'] = atms.apply(
                lambda row: calculate_distance(center_lat, center_lon, row['latitude'], row['longitude']), axis=1)
    
    candidate_atms = candidate_atms.sort_values(by='dist').head(50)
    
    if known_fraud_atm_id and known_fraud_atm_id not in candidate_atms['atm_id'].values:
        known_atm_row = atms[atms['atm_id'] == known_fraud_atm_id].copy()
        if not known_atm_row.empty:
            if len(candidate_atms) >= 50:
                candidate_atms = candidate_atms.iloc[:-1]
            candidate_atms = pd.concat([candidate_atms, known_atm_row])
                
    candidate_atms = candidate_atms.sort_values(by='dist').drop_duplicates(subset=['atm_id'])
    
    return candidate_atms.to_dict('records')

def generate_candidates(case_id: str, k_ring: int = 2) -> list:
    data_dir = get_data_dir()
    try:
        comps = pd.read_csv(os.path.join(data_dir, "complaints.csv"))
        atms = pd.read_csv(os.path.join(data_dir, "atms.csv"))
        wds = pd.read_csv(os.path.join(data_dir, "withdrawals.csv"))
    except FileNotFoundError:
        return []
    return generate_candidates_for_case(case_id, comps, atms, wds, k_ring)
