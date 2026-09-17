import logging
from datetime import datetime
from typing import List, Dict, Set
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Account, Withdrawal, ATM
from app.db.neo4j_session import get_neo4j_driver
from app.ml.feature_schemas import CandidateATM

logger = logging.getLogger(__name__)

class CandidateGenerator:
    def __init__(self, db: Session, max_candidates: int = 10):
        self.db = db
        self.max_candidates = max_candidates
        self.neo4j_driver = get_neo4j_driver()

    def generate_candidates(
        self, account_id: int, prediction_timestamp: datetime
    ) -> List[CandidateATM]:
        """
        Generates candidate ATMs securely without data leakage.
        """
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return []

        candidates_map: Dict[str, Set[str]] = {}
        spatial_distances: Dict[str, float] = {}

        def add_candidate(atm_id: str, reason: str):
            if atm_id not in candidates_map:
                candidates_map[atm_id] = set()
            candidates_map[atm_id].add(reason)

        # ---------------------------------------------------------
        # Stage 1: Historical candidates
        # ---------------------------------------------------------
        hist_withdrawals = self.db.query(Withdrawal.atm_id).filter(
            Withdrawal.account_id == account_id,
            Withdrawal.timestamp <= prediction_timestamp
        ).distinct().all()
        
        hist_atm_ids = [w[0] for w in hist_withdrawals]
        for atm_id in hist_atm_ids:
            add_candidate(atm_id, "Historical")

        # ---------------------------------------------------------
        # Stage 2: Syndicate candidates (Neo4j)
        # ---------------------------------------------------------
        syndicate_atm_ids = []
        if self.neo4j_driver:
            with self.neo4j_driver.session() as session:
                query = """
                MATCH path=(target:Account {account_number: $acc_num})<-[:TRANSFERRED_TO*1..2]-(mule:Account)
                MATCH (mule)-[:MADE_WITHDRAWAL]->(w:Withdrawal)-[:AT_ATM]->(atm:ATM)
                WHERE ALL(r IN relationships(path) WHERE r.timestamp IS NOT NULL AND datetime(r.timestamp) <= datetime($cutoff))
                  AND w.timestamp IS NOT NULL AND datetime(w.timestamp) <= datetime($cutoff)
                RETURN DISTINCT atm.atm_id AS atm_id
                """
                res = session.run(query, {
                    "acc_num": account.account_number,
                    "cutoff": prediction_timestamp.isoformat()
                })
                for record in res:
                    syndicate_atm_ids.append(record["atm_id"])
                    add_candidate(record["atm_id"], "Syndicate")

        # ---------------------------------------------------------
        # Stage 3: Spatial candidates
        # ---------------------------------------------------------
        anchor_atm_ids = set(hist_atm_ids + syndicate_atm_ids)
        if anchor_atm_ids:
            anchor_atms = self.db.query(ATM).filter(ATM.atm_id.in_(anchor_atm_ids)).all()
            for anchor in anchor_atms:
                if anchor.latitude is not None and anchor.longitude is not None:
                    # Find ATMs within 5km (5000 meters)
                    dist_expr = func.ST_DistanceSphere(
                        func.ST_SetSRID(func.ST_MakePoint(ATM.longitude, ATM.latitude), 4326),
                        func.ST_SetSRID(func.ST_MakePoint(anchor.longitude, anchor.latitude), 4326)
                    )
                    nearby_atms = self.db.query(ATM.atm_id, dist_expr.label('dist')).filter(
                        ATM.atm_id.notin_(anchor_atm_ids),
                        ATM.latitude.isnot(None),
                        ATM.longitude.isnot(None),
                        dist_expr <= 5000
                    ).order_by(dist_expr).limit(self.max_candidates).all()
                    
                    for nearby in nearby_atms:
                        atm_id = nearby[0]
                        dist = nearby[1]
                        add_candidate(atm_id, "Spatial")
                        if atm_id not in spatial_distances or dist < spatial_distances[atm_id]:
                            spatial_distances[atm_id] = dist

        # ---------------------------------------------------------
        # Stage 4: Fallback candidates
        # ---------------------------------------------------------
        if len(candidates_map) < self.max_candidates:
            # Hotspots: ATMs used by flagged accounts
            hotspots = self.db.query(
                Withdrawal.atm_id, func.count(Withdrawal.id).label('count')
            ).join(Account).filter(
                Account.is_flagged == True,
                Withdrawal.timestamp <= prediction_timestamp
            ).group_by(Withdrawal.atm_id).order_by(func.count(Withdrawal.id).desc()).limit(self.max_candidates).all()
            
            for hs in hotspots:
                if len(candidates_map) >= self.max_candidates:
                    break
                add_candidate(hs[0], "Fallback-Hotspot")

        if len(candidates_map) < self.max_candidates:
            # Absolute fallback: Just get existing active ATMs
            all_atms = self.db.query(ATM.atm_id).limit(self.max_candidates).all()
            for a in all_atms:
                if len(candidates_map) >= self.max_candidates:
                    break
                add_candidate(a[0], "Fallback-Global")

        # ---------------------------------------------------------
        # Build Results
        # ---------------------------------------------------------
        results = []
        for atm_id, reasons_set in candidates_map.items():
            results.append(CandidateATM(
                atm_id=atm_id,
                reasons=list(reasons_set)
            ))

        def score_reasons(reasons):
            score = 0
            if "Historical" in reasons: score += 1000
            if "Syndicate" in reasons: score += 100
            if "Spatial" in reasons: score += 10
            if "Fallback-Hotspot" in reasons: score += 1
            return score

        # Sort by relevance, then distance for spatial, then determinism (e.g. by atm_id) and limit
        results.sort(key=lambda x: (-score_reasons(x.reasons), spatial_distances.get(x.atm_id, float('inf')), x.atm_id))
        return results[:self.max_candidates]
