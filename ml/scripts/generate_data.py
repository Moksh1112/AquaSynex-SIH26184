import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_synthetic_data(data_dir: str):
    """Generates synthetic prototype data for the predictive cash-out system."""
    # Ensure reproducibility
    random.seed(42)
    np.random.seed(42)

    os.makedirs(data_dir, exist_ok=True)

    # Base timestamps
    base_time = datetime(2026, 9, 10, 12, 0, 0)
    
    # 1. Generate ATMs (centered around a mock Mumbai location: 19.076, 72.877)
    num_atms = 200
    atm_data = []
    base_lat, base_lon = 19.0760, 72.8770
    for i in range(1, num_atms + 1):
        atm_id = f"ATM-{i:03d}"
        # Spread them within ~10km (approx 0.1 degree)
        lat = base_lat + np.random.normal(0, 0.05)
        lon = base_lon + np.random.normal(0, 0.05)
        # Mock h3 index for now
        h3_index = f"mock_h3_{i}"
        atm_data.append({
            "atm_id": atm_id,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "h3_index": h3_index,
            "is_synthetic": True
        })
    df_atms = pd.DataFrame(atm_data)
    df_atms.to_csv(os.path.join(data_dir, "atms.csv"), index=False)

    # Ensure ATM-184 and ATM-092 exist near the base for C10231
    # We will override some of their locations
    df_atms.loc[df_atms['atm_id'] == 'ATM-184', ['latitude', 'longitude']] = [19.076, 72.877]
    df_atms.loc[df_atms['atm_id'] == 'ATM-092', ['latitude', 'longitude']] = [19.081, 72.882]
    # Add a few more nearby ATMs for top-5
    df_atms.loc[df_atms['atm_id'] == 'ATM-045', ['latitude', 'longitude']] = [19.078, 72.875]
    df_atms.loc[df_atms['atm_id'] == 'ATM-012', ['latitude', 'longitude']] = [19.075, 72.880]
    df_atms.loc[df_atms['atm_id'] == 'ATM-015', ['latitude', 'longitude']] = [19.077, 72.879]
    df_atms.to_csv(os.path.join(data_dir, "atms.csv"), index=False)


    # 2. Generate Accounts
    num_accounts = 1000
    account_data = []
    for i in range(1, num_accounts + 1):
        acc_id = f"ACC-{i:05d}"
        risk = round(np.random.uniform(0.0, 0.2), 2)
        account_data.append({
            "account_id": acc_id,
            "risk_score": risk,
            "is_synthetic": True
        })
    df_accounts = pd.DataFrame(account_data)

    # Specifically reserve ACC-09999 as the suspect account for C10231
    suspect_acc = "ACC-09999"
    df_accounts.loc[df_accounts.index == 999, 'account_id'] = suspect_acc
    df_accounts.loc[df_accounts.index == 999, 'risk_score'] = 0.95
    df_accounts.to_csv(os.path.join(data_dir, "accounts.csv"), index=False)


    # 3. Generate Transactions
    tx_data = []
    tx_id_counter = 1
    
    # Generate some normal background transactions
    for _ in range(5000):
        sender = f"ACC-{random.randint(1, num_accounts-1):05d}"
        receiver = f"ACC-{random.randint(1, num_accounts-1):05d}"
        if sender == receiver: continue
        amt = round(random.uniform(10, 500), 2)
        tx_time = base_time - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        tx_data.append({
            "tx_id": f"TX-{tx_id_counter:06d}",
            "sender_account_id": sender,
            "receiver_account_id": receiver,
            "amount": amt,
            "timestamp": tx_time.strftime("%Y-%m-%d %H:%M:%S"),
            "is_fraud": 0,
            "case_id": None,
            "is_synthetic": True
        })
        tx_id_counter += 1

    # Generate Fraud Sequence for C10231
    # Suspect account receives multiple recent inbound transactions rapidly
    fraud_time = datetime(2026, 9, 12, 18, 0, 0) # Base time for fraud burst
    for i in range(15):
        sender = f"ACC-{random.randint(1, num_accounts-1):05d}"
        amt = round(random.uniform(5000, 15000), 2)
        # Transactions occur in a tight 2-hour window
        tx_time = fraud_time + timedelta(minutes=random.randint(1, 120))
        tx_data.append({
            "tx_id": f"TX-{tx_id_counter:06d}",
            "sender_account_id": sender,
            "receiver_account_id": suspect_acc,
            "amount": amt,
            "timestamp": tx_time.strftime("%Y-%m-%d %H:%M:%S"),
            "is_fraud": 1,
            "case_id": "C10231",
            "is_synthetic": True
        })
        tx_id_counter += 1

    # Also add some transactions for another random case to have more than 1 case
    suspect_acc_2 = "ACC-08888"
    df_accounts.loc[df_accounts.index == 888, 'account_id'] = suspect_acc_2
    df_accounts.loc[df_accounts.index == 888, 'risk_score'] = 0.85
    fraud_time_2 = datetime(2026, 9, 11, 10, 0, 0)
    for i in range(8):
        sender = f"ACC-{random.randint(1, num_accounts-1):05d}"
        amt = round(random.uniform(1000, 5000), 2)
        tx_time = fraud_time_2 + timedelta(minutes=random.randint(1, 60))
        tx_data.append({
            "tx_id": f"TX-{tx_id_counter:06d}",
            "sender_account_id": sender,
            "receiver_account_id": suspect_acc_2,
            "amount": amt,
            "timestamp": tx_time.strftime("%Y-%m-%d %H:%M:%S"),
            "is_fraud": 1,
            "case_id": "C10222",
            "is_synthetic": True
        })
        tx_id_counter += 1

    df_accounts.to_csv(os.path.join(data_dir, "accounts.csv"), index=False)
    
    df_tx = pd.DataFrame(tx_data)
    df_tx.to_csv(os.path.join(data_dir, "transactions.csv"), index=False)


    # 4. Generate Withdrawals
    wd_data = []
    wd_id_counter = 1
    
    # Background withdrawals
    for _ in range(1000):
        acc = f"ACC-{random.randint(1, num_accounts-1):05d}"
        atm = f"ATM-{random.randint(1, num_atms):03d}"
        amt = round(random.uniform(100, 5000), 2)
        wd_time = base_time - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        wd_data.append({
            "withdrawal_id": f"WD-{wd_id_counter:06d}",
            "account_id": acc,
            "atm_id": atm,
            "amount": amt,
            "timestamp": wd_time.strftime("%Y-%m-%d %H:%M:%S"),
            "is_fraud": 0,
            "case_id": None,
            "is_synthetic": True
        })
        wd_id_counter += 1

    # Fraud withdrawal for C10231 (cash-out sequence shortly after inbound transactions)
    # The last inbound was around 2026-09-12 20:00:00, cashout at 22:30:00
    cashout_time = fraud_time + timedelta(hours=2, minutes=30)
    wd_data.append({
        "withdrawal_id": f"WD-{wd_id_counter:06d}",
        "account_id": suspect_acc,
        "atm_id": "ATM-184", # Chosen top candidate
        "amount": 100000.0,
        "timestamp": cashout_time.strftime("%Y-%m-%d %H:%M:%S"),
        "is_fraud": 1,
        "case_id": "C10231",
        "is_synthetic": True
    })
    wd_id_counter += 1

    # Fraud withdrawal for C10222
    cashout_time_2 = fraud_time_2 + timedelta(hours=1, minutes=15)
    wd_data.append({
        "withdrawal_id": f"WD-{wd_id_counter:06d}",
        "account_id": suspect_acc_2,
        "atm_id": "ATM-050",
        "amount": 20000.0,
        "timestamp": cashout_time_2.strftime("%Y-%m-%d %H:%M:%S"),
        "is_fraud": 1,
        "case_id": "C10222",
        "is_synthetic": True
    })
    wd_id_counter += 1

    df_wd = pd.DataFrame(wd_data)
    df_wd.to_csv(os.path.join(data_dir, "withdrawals.csv"), index=False)


    # 5. Generate Complaints
    comp_data = [
        {
            "case_id": "C10231",
            "account_id": suspect_acc,
            "fraud_amount": 100000.0,
            "timestamp": (cashout_time + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "is_synthetic": True
        },
        {
            "case_id": "C10222",
            "account_id": suspect_acc_2,
            "fraud_amount": 20000.0,
            "timestamp": (cashout_time_2 + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "is_synthetic": True
        }
    ]
    df_comp = pd.DataFrame(comp_data)
    df_comp.to_csv(os.path.join(data_dir, "complaints.csv"), index=False)

    print("Synthetic data generation complete.")
    print("Files created in:", data_dir)
    print("ATMs:", len(df_atms))
    print("Accounts:", len(df_accounts))
    print("Transactions:", len(df_tx))
    print("Withdrawals:", len(df_wd))
    print("Complaints:", len(df_comp))

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    data_dir = os.path.join(project_root, "ml", "data")
    generate_synthetic_data(data_dir)
