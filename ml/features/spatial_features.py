import pandas as pd
from spatial.geo.distance import calculate_distance

def extract_spatial_features(atm_row: pd.Series, suspect_acc: str, wds: pd.DataFrame, atms: pd.DataFrame, current_time: pd.Timestamp, candidate_atms: pd.DataFrame) -> dict:
    atm_lat = atm_row['latitude']
    atm_lon = atm_row['longitude']
    
    features = {}
    
    past_wds = wds[(wds['account_id'] == suspect_acc) & (wds['timestamp'] < current_time)]
    dist_prev = -1.0
    if not past_wds.empty:
        last_wd_atm = past_wds.sort_values('timestamp').iloc[-1]['atm_id']
        prev_atm_row = atms[atms['atm_id'] == last_wd_atm]
        if not prev_atm_row.empty:
            prev_lat = prev_atm_row.iloc[0]['latitude']
            prev_lon = prev_atm_row.iloc[0]['longitude']
            dist_prev = calculate_distance(prev_lat, prev_lon, atm_lat, atm_lon)
            
    features['distance_from_previous_withdrawal'] = dist_prev
    
    # Distance from case/suspect location
    center_lat = 19.076
    center_lon = 72.877
    features['distance_to_case_center'] = calculate_distance(center_lat, center_lon, atm_lat, atm_lon)
    
    # Number of nearby ATMs
    nearby = 0
    if not candidate_atms.empty:
        dists = candidate_atms.apply(lambda r: calculate_distance(atm_lat, atm_lon, r['latitude'], r['longitude']), axis=1)
        nearby = len(dists[dists <= 2.0]) - 1
    features['number_of_nearby_atms'] = max(0, nearby)
    
    # ATM proximity score
    dist = features['distance_to_case_center']
    features['atm_proximity_score'] = 1.0 / (dist + 0.1)
    
    return features
