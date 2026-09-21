import os
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.complaint import Complaint
from app.models.withdrawal import Withdrawal
from app.models.atm import ATM
from spatial.h3.h3_service import lat_lon_to_h3, get_nearby_cells
from spatial.geo.distance import calculate_distance
from app.models.account import Account

def get_data_dir() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    return os.path.join(project_root, "ml", "data")

def apply_distance_bands(candidates_list: list) -> list:
    """
    Applies distance-band sampling to a list of candidates.
    Candidates must be dictionaries containing at least 'atm_id' and 'dist' (in km).
    """
    if not candidates_list:
        return []
        
    df = pd.DataFrame(candidates_list)
    df = df.sort_values(by='dist').drop_duplicates(subset=['atm_id'])
    
    bands = [
        (0, 5, 80),
        (5, 10, 50),
        (10, 15, 40),
        (15, 20, 20),
        (20, 25, 10)
    ]
    
    selected_dfs = []
    selected_ids = set()
    
    for min_d, max_d, max_count in bands:
        if min_d == 0:
            band_df = df[(df['dist'] >= 0) & (df['dist'] <= max_d)]
        else:
            band_df = df[(df['dist'] > min_d) & (df['dist'] <= max_d)]
            
        band_selected = band_df.head(max_count)
        selected_dfs.append(band_selected)
        selected_ids.update(band_selected['atm_id'].tolist())
        
    final_df = pd.concat(selected_dfs) if selected_dfs else pd.DataFrame(columns=df.columns)
    
    if len(final_df) < 200:
        remaining = df[~df['atm_id'].isin(selected_ids)]
        needed = 200 - len(final_df)
        if needed > 0 and not remaining.empty:
            fill_df = remaining.head(needed)
            final_df = pd.concat([final_df, fill_df])
            
    final_df = final_df.sort_values(by='dist')
    return final_df.to_dict('records')

def generate_candidates_csv(case_id: str, k_ring: int = 2) -> list:
    data_dir = get_data_dir()
    try:
        comps = pd.read_csv(os.path.join(data_dir, "complaints.csv"), dtype={'case_id': str})
        atms = pd.read_csv(os.path.join(data_dir, "atms.csv"))
        wds = pd.read_csv(os.path.join(data_dir, "withdrawals.csv"), dtype={'case_id': str})
    except FileNotFoundError:
        return []

    case_comp = comps[comps['case_id'] == case_id]
    if case_comp.empty:
        return []

    wds['timestamp'] = pd.to_datetime(wds['timestamp'])
    current_time = pd.to_datetime(case_comp.iloc[0]['timestamp'])
    suspect_acc = case_comp.iloc[0]['account_id']



    center_lat = 19.076
    center_lon = 72.877

    # Non-leaking center: Suspect's last known legitimate withdrawal ATM
    past_wds = wds[(wds['account_id'] == suspect_acc) & (wds['timestamp'] < current_time) & (wds['is_fraud'] != 1)].sort_values('timestamp')
    if not past_wds.empty:
        last_wd_atm_id = past_wds.iloc[-1]['atm_id']
        last_atm = atms[atms['atm_id'] == last_wd_atm_id]
        if not last_atm.empty:
            center_lat = last_atm.iloc[0]['latitude']
            center_lon = last_atm.iloc[0]['longitude']

    center_h3 = lat_lon_to_h3(center_lat, center_lon, resolution=8)
    nearby_cells = get_nearby_cells(center_h3, k=k_ring)

    if 'current_h3' not in atms.columns:
        atms['current_h3'] = atms.apply(lambda row: lat_lon_to_h3(row['latitude'], row['longitude'], resolution=8), axis=1)

    candidate_atms = atms[atms['current_h3'].isin(nearby_cells)].copy()

    candidate_atms['dist'] = candidate_atms.apply(
        lambda row: calculate_distance(center_lat, center_lon, row['latitude'], row['longitude']), axis=1)

    if 'dist' not in atms.columns:
        atms['dist'] = atms.apply(
            lambda row: calculate_distance(center_lat, center_lon, row['latitude'], row['longitude']), axis=1)
    
    candidate_atms = atms[atms['dist'] <= 25.0].copy()
    cands_list = candidate_atms.to_dict('records')
    return apply_distance_bands(cands_list)

def generate_candidates(db: Session, case_id: str, k_ring: int = 2) -> list:
    """
    Generates candidate ATMs using PostgreSQL/PostGIS.
    """
    comp = db.query(Complaint).filter(Complaint.case_id == case_id).first()
    if not comp:
        return []



    center_lat = 19.076
    center_lon = 72.877

    # Non-leaking center: Suspect's last known legitimate withdrawal ATM
    account = db.query(Account).filter(Account.account_number == comp.account_id).first()
    
    past_wd = None
    if account:
        past_wd = db.query(Withdrawal).filter(
            Withdrawal.account_id == account.id,
            Withdrawal.timestamp < comp.reported_at,
            Withdrawal.is_fraud != 1
        ).order_by(Withdrawal.timestamp.desc()).first()
    
    if past_wd:
        past_atm = db.query(ATM).filter(ATM.atm_id == past_wd.atm_id).first()
        if past_atm:
            center_lat = past_atm.latitude
            center_lon = past_atm.longitude

    from sqlalchemy import text
    point = f'SRID=4326;POINT({center_lon} {center_lat})'

    # 25000 meters = 25km radius
    query = db.query(
        ATM,
        func.ST_DistanceSphere(text(f"ST_GeomFromEWKT('{point}')"), ATM.location).label('dist')
    ).filter(
        text(f"ST_DWithin(location::geography, ST_GeographyFromText('{point}'), 25000)")
    ).order_by('dist')

    try:
        results = query.all()
    except Exception as e:
        # Fallback to CSV if PostGIS fails or geometry is empty
        print(f"Error querying PostGIS: {e}")
        return generate_candidates_csv(case_id, k_ring)

    if not results:
        # Fallback if no local ATMs are mapped in DB
        return generate_candidates_csv(case_id, k_ring)

    candidates = []
    for atm, dist in results:
        candidates.append({
            'atm_id': atm.atm_id,
            'latitude': atm.latitude,
            'longitude': atm.longitude,
            'dist': dist / 1000.0  # standardize to km for distance bands
        })

    return apply_distance_bands(candidates)
