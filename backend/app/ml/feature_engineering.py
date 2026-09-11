from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Account, Transaction, Withdrawal, ATM
from app.db.neo4j_session import get_neo4j_driver
from app.ml.feature_schemas import CandidateFeatures

class FeatureEngineer:
    def __init__(self, db: Session):
        self.db = db
        self.neo4j_driver = get_neo4j_driver()

    def generate_features(
        self, 
        account_id: int, 
        candidate_atm_id: str, 
        prediction_timestamp: datetime
    ) -> CandidateFeatures:
        """
        Generates candidate-level features safely preventing data leakage by strictly
        adhering to the prediction_timestamp cutoff.
        """
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise ValueError(f"Account {account_id} not found")

        # ---------------------------------------------------------
        # A. Transaction Features
        # ---------------------------------------------------------
        inc_stats = self.db.query(
            func.count(Transaction.id),
            func.sum(Transaction.amount),
            func.max(Transaction.timestamp)
        ).filter(
            Transaction.receiver_account_id == account_id,
            Transaction.timestamp <= prediction_timestamp
        ).first()

        out_stats = self.db.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.sender_account_id == account_id,
            Transaction.timestamp <= prediction_timestamp
        ).first()

        transaction_count = inc_stats[0] or 0
        incoming_amount = inc_stats[1] or 0.0
        last_inc_time = inc_stats[2]
        outgoing_amount = out_stats[0] or 0.0

        time_since_last_transfer_hours = None
        if last_inc_time:
            delta = prediction_timestamp - last_inc_time
            time_since_last_transfer_hours = delta.total_seconds() / 3600.0

        # ---------------------------------------------------------
        # B. Graph Features
        # ---------------------------------------------------------
        upstream_account_count = 0
        if self.neo4j_driver:
            with self.neo4j_driver.session() as session:
                query = """
                MATCH (target:Account {account_number: $acc_num})<-[r:TRANSFERRED_TO]-(s:Account)
                WHERE r.timestamp IS NOT NULL AND datetime(r.timestamp) <= datetime($cutoff)
                RETURN count(DISTINCT s) AS upstream_count
                """
                res = session.run(query, {
                    "acc_num": account.account_number, 
                    "cutoff": prediction_timestamp.isoformat()
                }).single()
                
                if res:
                    upstream_account_count = res["upstream_count"]

        # ---------------------------------------------------------
        # C. Withdrawal Features
        # ---------------------------------------------------------
        w_stats = self.db.query(
            func.count(Withdrawal.id),
            func.sum(Withdrawal.amount),
            func.max(Withdrawal.timestamp)
        ).filter(
            Withdrawal.account_id == account_id,
            Withdrawal.timestamp <= prediction_timestamp
        ).first()

        historical_withdrawal_count = w_stats[0] or 0
        total_withdrawn_amount = w_stats[1] or 0.0
        last_withdrawal_time = w_stats[2]

        prev_atm_use = self.db.query(func.count(Withdrawal.id)).filter(
            Withdrawal.account_id == account_id,
            Withdrawal.atm_id == candidate_atm_id,
            Withdrawal.timestamp <= prediction_timestamp
        ).scalar() or 0

        # ---------------------------------------------------------
        # D. Spatial Features
        # ---------------------------------------------------------
        distance_to_last_withdrawal_meters = None
        if historical_withdrawal_count > 0:
            last_w = self.db.query(Withdrawal).filter(
                Withdrawal.account_id == account_id,
                Withdrawal.timestamp <= prediction_timestamp
            ).order_by(Withdrawal.timestamp.desc()).first()

            if last_w:
                last_atm = self.db.query(ATM).filter(ATM.atm_id == last_w.atm_id).first()
                cand_atm = self.db.query(ATM).filter(ATM.atm_id == candidate_atm_id).first()
                
                if last_atm and cand_atm:
                    dist = self.db.query(
                        func.ST_DistanceSphere(
                            func.ST_SetSRID(func.ST_MakePoint(cand_atm.longitude, cand_atm.latitude), 4326),
                            func.ST_SetSRID(func.ST_MakePoint(last_atm.longitude, last_atm.latitude), 4326)
                        )
                    ).scalar()
                    distance_to_last_withdrawal_meters = dist

        # ---------------------------------------------------------
        # E. Temporal Features
        # ---------------------------------------------------------
        hour_of_day = prediction_timestamp.hour
        day_of_week = prediction_timestamp.weekday()
        
        time_since_last_withdrawal_hours = None
        if last_withdrawal_time:
            delta = prediction_timestamp - last_withdrawal_time
            time_since_last_withdrawal_hours = delta.total_seconds() / 3600.0

        return CandidateFeatures(
            account_id=account_id,
            candidate_atm_id=candidate_atm_id,
            prediction_timestamp=prediction_timestamp,
            transaction_count=transaction_count,
            incoming_amount=incoming_amount,
            outgoing_amount=outgoing_amount,
            time_since_last_transfer_hours=time_since_last_transfer_hours,
            upstream_account_count=upstream_account_count,
            historical_withdrawal_count=historical_withdrawal_count,
            total_withdrawn_amount=total_withdrawn_amount,
            previous_use_of_candidate_atm=prev_atm_use,
            distance_to_last_withdrawal_meters=distance_to_last_withdrawal_meters,
            hour_of_day=hour_of_day,
            day_of_week=day_of_week,
            time_since_last_withdrawal_hours=time_since_last_withdrawal_hours
        )
