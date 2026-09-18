import os
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.orm import aliased
from app.models.complaint import Complaint
from app.models.transaction import Transaction
from app.models.withdrawal import Withdrawal
from app.models.atm import ATM
from app.models.account import Account

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
    comps = pd.read_csv(os.path.join(data_dir, "complaints.csv"), dtype={'case_id': str})
    atms = pd.read_csv(os.path.join(data_dir, "atms.csv"))
    txs = pd.read_csv(os.path.join(data_dir, "transactions.csv"), parse_dates=['timestamp'], dtype={'case_id': str})
    wds = pd.read_csv(os.path.join(data_dir, "withdrawals.csv"), parse_dates=['timestamp'], dtype={'case_id': str})

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
        fraud_atm = case_wds.iloc[0]['atm_id']
    else:
        fraud_atm = None

    current_time = pd.to_datetime(case_comp.iloc[0]['timestamp'])

    tx_feats = extract_transaction_features(suspect_acc, txs, current_time)
    temp_feats = extract_temporal_features(suspect_acc, txs, wds, current_time)
    beh_feats = extract_behavioral_features(suspect_acc, txs, wds, current_time)
    graph_feats = extract_graph_features(suspect_acc, txs, wds, current_time)

    base_features = {**tx_feats, **temp_feats, **beh_feats, **graph_feats}

    df_cands = pd.DataFrame(candidate_atms)

    cand_atm_ids = df_cands['atm_id'].tolist()
    past_global_wds = wds[(wds['timestamp'] < current_time) & (wds['case_id'] != case_id) & (wds['atm_id'].isin(cand_atm_ids))]
    
    atm_stats = {}
    for atm_id in cand_atm_ids:
        atm_wds = past_global_wds[past_global_wds['atm_id'] == atm_id]
        wd_count = len(atm_wds)
        fraud_count = len(atm_wds[atm_wds['is_fraud'] == 1])
        fraud_rate = fraud_count / (wd_count + 1.0)
        
        days_since = -1.0
        if not atm_wds.empty:
            last_time = atm_wds['timestamp'].max()
            days_since = (current_time - last_time).total_seconds() / 86400.0
            
        atm_stats[atm_id] = {
            'atm_global_withdrawal_count': wd_count,
            'atm_global_fraud_count': fraud_count,
            'atm_global_fraud_rate': fraud_rate,
            'atm_days_since_last_activity': days_since
        }

    rows = []

    for atm_cand in candidate_atms:
        row = {'case_id': case_id, 'atm_id': atm_cand['atm_id']}
        row['label'] = 1 if atm_cand['atm_id'] == fraud_atm else 0

        sp_feats = extract_spatial_features(pd.Series(atm_cand), suspect_acc, wds, atms, current_time, df_cands)

        row.update(base_features)
        row.update(sp_feats)
        row.update(atm_stats[atm_cand['atm_id']])
        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.fillna(0.0)

    return df

def build_features(db: Session, case_id: str, candidate_atms: list) -> pd.DataFrame:
    """
    Build features using data retrieved directly from PostgreSQL.
    """
    comp = db.query(Complaint).filter(Complaint.case_id == case_id).first()
    if not comp:
        return pd.DataFrame()

    comps_df = pd.DataFrame([{
        'case_id': comp.case_id,
        'account_id': comp.account_id,
        'timestamp': comp.reported_at
    }])

    # ATMs
    atms_df = pd.read_sql(db.query(ATM).statement, db.bind)

    # Withdrawals (join to get account_number as account_id)
    wds_query = db.query(
        Withdrawal.id.label('wd_id'),
        Account.account_number.label('account_id'),
        Withdrawal.atm_id,
        Withdrawal.amount,
        Withdrawal.timestamp,
        Withdrawal.is_fraud,
        Withdrawal.case_id
    ).join(Account, Withdrawal.account_id == Account.id)
    wds_df = pd.read_sql(wds_query.statement, db.bind)

    # Transactions (join to get sender and receiver account numbers)
    SenderAcc = aliased(Account)
    ReceiverAcc = aliased(Account)
    txs_query = db.query(
        Transaction.id.label('tx_id'),
        SenderAcc.account_number.label('sender_account_id'),
        ReceiverAcc.account_number.label('receiver_account_id'),
        Transaction.amount,
        Transaction.timestamp
    ).join(SenderAcc, Transaction.sender_account_id == SenderAcc.id) \
     .join(ReceiverAcc, Transaction.receiver_account_id == ReceiverAcc.id)
    txs_df = pd.read_sql(txs_query.statement, db.bind)

    # Add dummy columns for compatibility with offline CSV logic if missing
    if 'is_fraud' not in txs_df.columns:
        txs_df['is_fraud'] = 0
    if 'case_id' not in txs_df.columns:
        txs_df['case_id'] = None

    if not txs_df.empty:
        txs_df['timestamp'] = pd.to_datetime(txs_df['timestamp'])
        txs_df = txs_df.sort_values('timestamp')

    if not wds_df.empty:
        wds_df['timestamp'] = pd.to_datetime(wds_df['timestamp'])
        wds_df = wds_df.sort_values('timestamp')

    return build_features_for_case(case_id, candidate_atms, comps_df, atms_df, txs_df, wds_df)
