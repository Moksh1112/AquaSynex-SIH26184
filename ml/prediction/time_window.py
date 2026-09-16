import os
import pandas as pd

def get_data_dir() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    return os.path.join(project_root, "ml", "data")

def predict_time_window(case_id: str) -> str:
    data_dir = get_data_dir()
    try:
        comps = pd.read_csv(os.path.join(data_dir, "complaints.csv"), dtype={'case_id': str})
        wds = pd.read_csv(os.path.join(data_dir, "withdrawals.csv"), parse_dates=['timestamp'], dtype={'case_id': str})
        txs = pd.read_csv(os.path.join(data_dir, "transactions.csv"), parse_dates=['timestamp'], dtype={'case_id': str})
    except FileNotFoundError:
        return "Insufficient historical data"
        
    case_comp = comps[comps['case_id'] == case_id]
    if case_comp.empty:
        return "Insufficient historical data"
        
    suspect_acc = case_comp.iloc[0]['account_id']
    
    # Check withdrawals first
    acc_wds = wds[wds['account_id'] == suspect_acc]
    if not acc_wds.empty:
        hours = acc_wds['timestamp'].dt.hour
        most_common = hours.mode()
        if not most_common.empty:
            hour = most_common.iloc[0]
            return f"{hour:02d}:00-{(hour+1)%24:02d}:00"
            
    # Fallback to transactions
    inbound = txs[txs['receiver_account_id'] == suspect_acc]
    outbound = txs[txs['sender_account_id'] == suspect_acc]
    acc_txs = pd.concat([inbound, outbound])
    
    if not acc_txs.empty:
        hours = acc_txs['timestamp'].dt.hour
        most_common = hours.mode()
        if not most_common.empty:
            hour = most_common.iloc[0]
            return f"{hour:02d}:00-{(hour+1)%24:02d}:00"
            
    return "Insufficient historical data"
