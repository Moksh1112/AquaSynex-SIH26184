import pandas as pd

def extract_temporal_features(suspect_acc: str, txs: pd.DataFrame, wds: pd.DataFrame, current_time: pd.Timestamp) -> dict:
    """
    Extracts temporal features relative to current_time.
    """
    features = {
        'hour_of_day': current_time.hour,
        'day_of_week': current_time.dayofweek,
        'is_weekend': int(current_time.dayofweek >= 5),
        'is_night': int(current_time.hour < 6 or current_time.hour >= 22)
    }
    
    past_txs = txs[(txs['receiver_account_id'] == suspect_acc) & (txs['timestamp'] < current_time)]
    
    last_1h_time = current_time - pd.Timedelta(hours=1)
    last_24h_time = current_time - pd.Timedelta(hours=24)
    
    features['transactions_last_1h'] = len(past_txs[past_txs['timestamp'] >= last_1h_time])
    features['transactions_last_24h'] = len(past_txs[past_txs['timestamp'] >= last_24h_time])
    
    past_wds = wds[(wds['account_id'] == suspect_acc) & (wds['timestamp'] < current_time)]
    features['withdrawals_last_24h'] = len(past_wds[past_wds['timestamp'] >= last_24h_time])
    
    time_since = -1.0 # default if no prior tx
    if not past_txs.empty:
        last_tx_time = past_txs['timestamp'].max()
        time_since = (current_time - last_tx_time).total_seconds() / 3600.0
    
    features['time_since_last_transaction'] = time_since
    
    return features
