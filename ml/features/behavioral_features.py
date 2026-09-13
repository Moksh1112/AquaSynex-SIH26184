import pandas as pd

def extract_behavioral_features(suspect_acc: str, txs: pd.DataFrame, wds: pd.DataFrame, current_time: pd.Timestamp) -> dict:
    past_txs = txs[(txs['receiver_account_id'] == suspect_acc) & (txs['timestamp'] < current_time)]
    
    amt_dev = 0.0
    vel = 0.0
    unusual = 0
    if not past_txs.empty:
        mean_amt = past_txs['amount'].mean()
        if len(past_txs) >= 3:
            recent_amt = past_txs.iloc[-1]['amount']
            amt_dev = recent_amt - mean_amt
            unusual = 1 if amt_dev > mean_amt * 2 else 0
        
        min_time = past_txs['timestamp'].min()
        days_active = max(1.0, (current_time - min_time).total_seconds() / 86400.0)
        vel = len(past_txs) / days_active
        
    past_wds = wds[(wds['account_id'] == suspect_acc) & (wds['timestamp'] < current_time)]
    wd_freq = 0.0
    if not past_wds.empty:
        min_time_wd = past_wds['timestamp'].min()
        days_active_wd = max(1.0, (current_time - min_time_wd).total_seconds() / 86400.0)
        wd_freq = len(past_wds) / days_active_wd
        
    recent_activity_score = vel + wd_freq + (unusual * 5.0)
    
    return {
        'amount_deviation_from_avg': amt_dev,
        'transaction_velocity': vel,
        'unusual_transaction_indicator': unusual,
        'withdrawal_frequency': wd_freq,
        'recent_activity_score': recent_activity_score
    }
