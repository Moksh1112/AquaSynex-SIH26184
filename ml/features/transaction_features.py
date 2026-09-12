import pandas as pd

def extract_transaction_features(suspect_acc: str, txs: pd.DataFrame, current_time: pd.Timestamp) -> dict:
    """
    Extracts transaction features for the suspect account prior to the current_time.
    """
    past_txs = txs[txs['timestamp'] < current_time]
    
    inbound = past_txs[past_txs['receiver_account_id'] == suspect_acc]
    outbound = past_txs[past_txs['sender_account_id'] == suspect_acc]
    
    inbound_count = len(inbound)
    outbound_count = len(outbound)
    
    total_tx_amt = inbound['amount'].sum() + outbound['amount'].sum()
    avg_tx_amt = 0.0
    max_tx_amt = 0.0
    high_value_count = 0
    
    if inbound_count > 0:
        avg_tx_amt = inbound['amount'].mean()
        max_tx_amt = inbound['amount'].max()
        high_value_count = len(inbound[inbound['amount'] > 5000])
        
    return {
        'transaction_count': inbound_count + outbound_count,
        'total_transaction_amount': total_tx_amt,
        'average_transaction_amount': avg_tx_amt,
        'maximum_transaction_amount': max_tx_amt,
        'high_value_transaction_count': high_value_count,
        'inbound_transaction_count': inbound_count,
        'outbound_transaction_count': outbound_count
    }
