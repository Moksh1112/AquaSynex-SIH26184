import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time

def generate_synthetic_data(data_dir: str):
    print("Starting large-scale synthetic data generation...")
    start_time = time.time()
    
    random.seed(42)
    np.random.seed(42)
    os.makedirs(data_dir, exist_ok=True)
    
    base_time = datetime(2026, 9, 10, 12, 0, 0)
    base_ts = pd.Timestamp(base_time).value // 10**9 # in seconds
    
    # 1. ATMs
    num_atms = 1500
    atm_ids = np.array([f"ATM-{i:04d}" for i in range(1, num_atms + 1)])
    lats = np.random.normal(19.076, 0.05, num_atms)
    lons = np.random.normal(72.877, 0.05, num_atms)
    
    df_atms = pd.DataFrame({
        'atm_id': atm_ids,
        'latitude': np.round(lats, 6),
        'longitude': np.round(lons, 6),
        'h3_index': [f"mock_h3_{i}" for i in range(num_atms)],
        'is_synthetic': True
    })
    
    # Hardcode for C10231 validation
    df_atms.loc[df_atms['atm_id'] == 'ATM-0184', ['latitude', 'longitude']] = [19.076, 72.877]
    df_atms.loc[df_atms['atm_id'] == 'ATM-0092', ['latitude', 'longitude']] = [19.081, 72.882]
    df_atms.loc[df_atms['atm_id'] == 'ATM-0045', ['latitude', 'longitude']] = [19.078, 72.875]
    df_atms.loc[df_atms['atm_id'] == 'ATM-0012', ['latitude', 'longitude']] = [19.075, 72.880]
    df_atms.loc[df_atms['atm_id'] == 'ATM-0015', ['latitude', 'longitude']] = [19.077, 72.879]
    df_atms.to_csv(os.path.join(data_dir, "atms.csv"), index=False)
    
    # 2. Accounts
    num_accs = 8000
    acc_ids = np.array([f"ACC-{i:05d}" for i in range(1, num_accs + 1)])
    risks = np.random.uniform(0.0, 0.2, num_accs)
    
    df_accounts = pd.DataFrame({
        'account_id': acc_ids,
        'risk_score': np.round(risks, 2),
        'is_synthetic': True
    })
    
    # Reserve ACC-09999 for C10231
    if "ACC-09999" not in acc_ids:
        df_accounts = pd.concat([df_accounts, pd.DataFrame([{
            'account_id': "ACC-09999", 'risk_score': 0.95, 'is_synthetic': True
        }])], ignore_index=True)
        acc_ids = df_accounts['account_id'].values
    
    df_accounts.loc[df_accounts['account_id'] == 'ACC-09999', 'risk_score'] = 0.95
    
    # Assign home locations to accounts (same distribution as ATMs)
    acc_lats = np.random.normal(19.076, 0.05, len(df_accounts))
    acc_lons = np.random.normal(72.877, 0.05, len(df_accounts))
    df_accounts['home_lat'] = acc_lats
    df_accounts['home_lon'] = acc_lons
    
    df_accounts.to_csv(os.path.join(data_dir, "accounts.csv"), index=False)
    
    # Pre-calculate ATM coordinates for fast distance calculation
    atm_coords = df_atms[['latitude', 'longitude']].values
    
    # Designate 10% of ATMs as 'fraud hubs'
    num_hubs = int(num_atms * 0.10)
    fraud_hubs = set(np.random.choice(atm_ids, num_hubs, replace=False))
    
    # 3. Transactions (Background)
    num_txs = 600000
    tx_senders = np.random.choice(acc_ids, num_txs)
    tx_receivers = np.random.choice(acc_ids, num_txs)
    tx_amounts = np.random.uniform(10, 1000, num_txs)
    
    # Vectorized random timestamps over the last 30 days
    offsets = np.random.randint(0, 30 * 24 * 3600, num_txs)
    tx_timestamps = pd.to_datetime(base_ts - offsets, unit='s')
    
    df_tx = pd.DataFrame({
        'tx_id': [f"TX-{i:07d}" for i in range(1, num_txs + 1)],
        'sender_account_id': tx_senders,
        'receiver_account_id': tx_receivers,
        'amount': np.round(tx_amounts, 2),
        'timestamp': tx_timestamps,
        'is_fraud': 0,
        'case_id': None,
        'is_synthetic': True
    })
    
    # Remove self-loops
    df_tx = df_tx[df_tx['sender_account_id'] != df_tx['receiver_account_id']]
    
    # 4. Withdrawals (Background)
    num_wds = 150000
    wd_accs = np.random.choice(acc_ids, num_wds)
    
    # Assign legitimate ATMs close to account homes (within ~2km)
    wd_atms = []
    acc_dict = df_accounts.set_index('account_id').to_dict('index')
    
    print("Assigning legitimate withdrawals to nearby ATMs...")
    # Fast assignment: pick a random ATM, if it's too far, pick another. Or just add noise to home coords and find nearest.
    for acc in wd_accs:
        # Add small noise (approx 1-2km) to home
        lat = acc_dict[acc]['home_lat'] + np.random.normal(0, 0.01)
        lon = acc_dict[acc]['home_lon'] + np.random.normal(0, 0.01)
        # Find nearest ATM
        dists = (atm_coords[:, 0] - lat)**2 + (atm_coords[:, 1] - lon)**2
        nearest_idx = np.argmin(dists)
        wd_atms.append(atm_ids[nearest_idx])
        
    wd_amounts = np.random.uniform(100, 5000, num_wds)
    offsets_wd = np.random.randint(0, 30 * 24 * 3600, num_wds)
    wd_timestamps = pd.to_datetime(base_ts - offsets_wd, unit='s')
    
    df_wds = pd.DataFrame({
        'withdrawal_id': [f"WD-{i:07d}" for i in range(1, num_wds + 1)],
        'account_id': wd_accs,
        'atm_id': wd_atms,
        'amount': np.round(wd_amounts, 2),
        'timestamp': wd_timestamps,
        'is_fraud': 0,
        'case_id': None,
        'is_synthetic': True
    })
    
    # 5. Fraud Cases
    num_cases = 5000
    fraud_ratio = 0.15
    num_fraud = int(num_cases * fraud_ratio)
    
    case_ids = [f"C{10000 + i}" for i in range(num_cases)]
    # Ensure C10231 is a fraud case
    if "C10231" not in case_ids:
        case_ids[0] = "C10231"
        
    fraud_cases = set(np.random.choice(case_ids, num_fraud, replace=False))
    fraud_cases.add("C10231")
    
    suspect_accs = np.random.choice(acc_ids, num_cases, replace=False)
    case_to_acc = dict(zip(case_ids, suspect_accs))
    case_to_acc["C10231"] = "ACC-09999"
    
    fraud_txs = []
    fraud_wds = []
    complaints = []
    
    tx_id_ctr = num_txs + 1
    wd_id_ctr = num_wds + 1
    
    for case_id in case_ids:
        acc = case_to_acc[case_id]
        is_fraud = case_id in fraud_cases
        
        case_time = base_time - timedelta(days=random.randint(1, 28), hours=random.randint(0, 23))
        
        if is_fraud:
            # Fraud Burst
            burst_size = random.randint(5, 15)
            for _ in range(burst_size):
                fraud_txs.append({
                    'tx_id': f"TX-{tx_id_ctr:07d}",
                    'sender_account_id': np.random.choice(acc_ids),
                    'receiver_account_id': acc,
                    'amount': round(random.uniform(5000, 20000), 2),
                    'timestamp': case_time - timedelta(minutes=random.randint(30, 180)),
                    'is_fraud': 1,
                    'case_id': case_id,
                    'is_synthetic': True
                })
                tx_id_ctr += 1
                
            # Cashout WD
            # Fraudster travels 2-20km away from victim's home. 
            # 80% chance they use a known 'fraud hub'.
            h_lat = acc_dict[acc]['home_lat']
            h_lon = acc_dict[acc]['home_lon']
            
            # Distance offset (approx 2-20km)
            angle = np.random.uniform(0, 2 * np.pi)
            dist_deg = np.random.uniform(0.02, 0.18) 
            f_lat = h_lat + dist_deg * np.sin(angle)
            f_lon = h_lon + dist_deg * np.cos(angle)
            
            # Find closest ATM to this fraud target location
            dists = (atm_coords[:, 0] - f_lat)**2 + (atm_coords[:, 1] - f_lon)**2
            
            if random.random() < 0.80:
                # Restrict to fraud hubs
                hub_mask = np.isin(atm_ids, list(fraud_hubs))
                dists[~hub_mask] = np.inf
                
            fraud_idx = np.argmin(dists)
            fraud_atm = atm_ids[fraud_idx]
            
            if case_id == "C10231":
                fraud_atm = "ATM-0184"
                
            fraud_amt = round(random.uniform(20000, 100000), 2)
            fraud_wds.append({
                'withdrawal_id': f"WD-{wd_id_ctr:07d}",
                'account_id': acc,
                'atm_id': fraud_atm,
                'amount': fraud_amt,
                'timestamp': case_time,
                'is_fraud': 1,
                'case_id': case_id,
                'is_synthetic': True
            })
            wd_id_ctr += 1
            
            complaints.append({
                'case_id': case_id,
                'account_id': acc,
                'fraud_amount': fraud_amt,
                'timestamp': case_time + timedelta(days=1),
                'is_synthetic': True
            })
        else:
            # Normal case (complaint filed but no fraud, just a false alarm)
            # Maybe some large transaction triggered it
            complaints.append({
                'case_id': case_id,
                'account_id': acc,
                'fraud_amount': round(random.uniform(5000, 15000), 2),
                'timestamp': case_time + timedelta(days=1),
                'is_synthetic': True
            })
            
    df_tx = pd.concat([df_tx, pd.DataFrame(fraud_txs)], ignore_index=True)
    df_tx.to_csv(os.path.join(data_dir, "transactions.csv"), index=False)
    
    df_wds = pd.concat([df_wds, pd.DataFrame(fraud_wds)], ignore_index=True)
    df_wds.to_csv(os.path.join(data_dir, "withdrawals.csv"), index=False)
    
    df_comp = pd.DataFrame(complaints)
    df_comp.to_csv(os.path.join(data_dir, "complaints.csv"), index=False)
    
    print(f"Data generation finished in {time.time() - start_time:.2f} seconds.")
    print(f"Cases: {len(df_comp)} (Fraud: {len(fraud_cases)})")
    print(f"ATMs: {len(df_atms)}")
    print(f"Accounts: {len(df_accounts)}")
    print(f"Transactions: {len(df_tx)}")
    print(f"Withdrawals: {len(df_wds)}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    data_dir = os.path.join(project_root, "ml", "data")
    generate_synthetic_data(data_dir)
