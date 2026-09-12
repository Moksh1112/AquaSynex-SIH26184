import os
import pandas as pd

from ml.features.transaction_features import extract_transaction_features
from ml.features.temporal_features import extract_temporal_features
from ml.features.spatial_features import extract_spatial_features
from ml.features.behavioral_features import extract_behavioral_features
from ml.features.graph_features import extract_graph_features

def get_data_dir() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    return os.path.join(project_root, "ml", "data")

def load_datasets():
    data_dir = get_data_dir()
    comps = pd.read_csv(os.path.join(data_dir, "complaints.csv"))
    atms = pd.read_csv(os.path.join(data_dir, "atms.csv"))
    txs = pd.read_csv(os.path.join(data_dir, "transactions.csv"), parse_dates=['timestamp'])
    wds = pd.read_csv(os.path.join(data_dir, "withdrawals.csv"), parse_dates=['timestamp'])
    
    # Sort for time-based operations
    txs = txs.sort_values('timestamp')
    wds = wds.sort_values('timestamp')
    return comps, atms, txs, wds

def build_features_for_case(case_id: str, candidate_atms: list, comps, atms, txs, wds) -> pd.DataFrame:
    if not candidate_atms:
        return pd.DataFrame()
        
    case_comp = comps[comps['case_id'] == case_id]
    if case_comp.empty:
        return pd.DataFrame()
        
    suspect_acc = case_comp.iloc[0]['account_id']
    
    case_wds = wds[(wds['case_id'] == case_id) & (wds['is_fraud'] == 1)]
    if not case_wds.empty:
        current_time = case_wds['timestamp'].min()
        fraud_atm = case_wds.iloc[0]['atm_id']
    else:
        current_time = pd.to_datetime(case_comp.iloc[0]['timestamp'])
        fraud_atm = None
        
    tx_feats = extract_transaction_features(suspect_acc, txs, current_time)
    temp_feats = extract_temporal_features(suspect_acc, txs, wds, current_time)
    beh_feats = extract_behavioral_features(suspect_acc, txs, wds, current_time)
    graph_feats = extract_graph_features(suspect_acc, txs, wds, current_time)
    
    base_features = {**tx_feats, **temp_feats, **beh_feats, **graph_feats}
    
    rows = []
    df_cands = pd.DataFrame(candidate_atms)
    
    for atm_cand in candidate_atms:
        row = {'case_id': case_id, 'atm_id': atm_cand['atm_id']}
        row['label'] = 1 if atm_cand['atm_id'] == fraud_atm else 0
        
        sp_feats = extract_spatial_features(pd.Series(atm_cand), suspect_acc, wds, atms, current_time, df_cands)
        
        row.update(base_features)
        row.update(sp_feats)
        rows.append(row)
        
    df = pd.DataFrame(rows)
    df = df.fillna(0.0)
    
    return df

def build_features(case_id: str, candidate_atms: list) -> pd.DataFrame:
    # Kept for backward compatibility for single-case calls
    comps, atms, txs, wds = load_datasets()
    return build_features_for_case(case_id, candidate_atms, comps, atms, txs, wds)
