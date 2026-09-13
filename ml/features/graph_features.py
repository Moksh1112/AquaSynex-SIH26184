import pandas as pd

def extract_graph_features(suspect_acc: str, txs: pd.DataFrame, wds: pd.DataFrame, current_time: pd.Timestamp) -> dict:
    past_txs = txs[txs['timestamp'] < current_time]
    
    inbound = past_txs[past_txs['receiver_account_id'] == suspect_acc]
    outbound = past_txs[past_txs['sender_account_id'] == suspect_acc]
    
    unique_senders = inbound['sender_account_id'].nunique()
    unique_receivers = outbound['receiver_account_id'].nunique()
    unique_counterparties = unique_senders + unique_receivers
    
    past_wds = wds[(wds['account_id'] == suspect_acc) & (wds['timestamp'] < current_time)]
    unique_atms = past_wds['atm_id'].nunique()
    
    return {
        'account_transaction_count': len(inbound) + len(outbound),
        'account_atm_count': unique_atms,
        'account_unique_counterparties': unique_counterparties,
        'account_network_activity': len(inbound) + len(outbound) + unique_counterparties
    }
