import pandas as pd
from spatial.geo.distance import calculate_distance

def extract_spatial_features(atm_row: pd.Series, suspect_acc: str, wds: pd.DataFrame, atms: pd.DataFrame, current_time: pd.Timestamp, candidate_atms: pd.DataFrame) -> dict:
    atm_lat = atm_row['latitude']
    atm_lon = atm_row['longitude']
    
    features = {}
    
    # Identify the actual case center (suspect's last known legitimate withdrawal ATM)
    past_wds = wds[(wds['account_id'] == suspect_acc) & (wds['timestamp'] < current_time) & (wds['is_fraud'] != 1)]
    
    center_lat = 19.076  # Default fallback
    center_lon = 72.877
    dist_prev = -1.0
    
    if not past_wds.empty:
        last_wd = past_wds.sort_values('timestamp').iloc[-1]
        last_wd_atm = last_wd['atm_id']
        prev_atm_row = atms[atms['atm_id'] == last_wd_atm]
        if not prev_atm_row.empty:
            center_lat = prev_atm_row.iloc[0]['latitude']
            center_lon = prev_atm_row.iloc[0]['longitude']
            dist_prev = calculate_distance(center_lat, center_lon, atm_lat, atm_lon)
            
    features['distance_from_previous_withdrawal'] = dist_prev
    features['distance_to_case_center'] = calculate_distance(center_lat, center_lon, atm_lat, atm_lon)
    
    # Number of nearby ATMs in the candidate pool
    nearby = 0
    if not candidate_atms.empty:
        dists = candidate_atms.apply(lambda r: calculate_distance(atm_lat, atm_lon, r['latitude'], r['longitude']), axis=1)
        nearby = len(dists[dists <= 2.0]) - 1
    features['number_of_nearby_atms'] = max(0, nearby)
    
    # ATM proximity score (using true center)
    dist = features['distance_to_case_center']
    features['atm_proximity_score'] = 1.0 / (dist + 0.1)

    # Candidate-specific historical interactions
    past_wds_at_atm = past_wds[past_wds['atm_id'] == atm_row['atm_id']]
    features['previous_withdrawals_at_this_atm'] = len(past_wds_at_atm)
    features['has_visited_this_atm'] = 1 if len(past_wds_at_atm) > 0 else 0
    
    time_since_visit = -1.0
    if not past_wds_at_atm.empty:
        last_visit_time = past_wds_at_atm['timestamp'].max()
        time_since_visit = (current_time - last_visit_time).total_seconds() / 3600.0
    features['time_since_last_visit'] = time_since_visit
    
    atm_freq = 0.0
    if not past_wds.empty:
        atm_freq = len(past_wds_at_atm) / len(past_wds)
    features['atm_historical_frequency'] = atm_freq
    
    return features
