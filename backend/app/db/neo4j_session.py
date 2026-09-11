import logging
from neo4j import GraphDatabase, exceptions
from app.core.config import settings

logger = logging.getLogger(__name__)

class Neo4jConnection:
    def __init__(self, uri, user, pwd):
        self.uri = uri
        self.user = user
        self.pwd = pwd
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.pwd))
            self.driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j")
        except exceptions.ServiceUnavailable as e:
            logger.error(f"Failed to create Neo4j driver: {e}")
            self.driver = None
        except Exception as e:
            logger.error(f"Neo4j connection error: {e}")
            self.driver = None

    def close(self):
        if self.driver is not None:
            self.driver.close()

    def query(self, query, parameters=None, db=None):
        if self.driver is None:
            logger.error("Driver not initialized!")
            return None
            
        assert self.driver is not None
        session = None
        response = None
        try:
            session = self.driver.session(database=db) if db else self.driver.session()
            response = list(session.run(query, parameters))
        except Exception as e:
            logger.error(f"Query failed: {e}")
        finally:
            if session is not None:
                session.close()
        return response
        
    def setup_constraints(self):
        """Sets up unique constraints ensuring idempotent behavior."""
        if self.driver is None:
            return
            
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Account) REQUIRE n.account_number IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Transaction) REQUIRE n.transaction_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Withdrawal) REQUIRE n.withdrawal_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:ATM) REQUIRE n.atm_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Complaint) REQUIRE n.case_id IS UNIQUE"
        ]
        
        for c in constraints:
            self.query(c)

neo4j_conn = Neo4jConnection(settings.NEO4J_URI, settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)

def get_neo4j_driver():
    return neo4j_conn.driver

def init_neo4j():
    neo4j_conn.setup_constraints()
