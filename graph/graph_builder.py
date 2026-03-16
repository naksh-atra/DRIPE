import os
import logging
from typing import List, Optional
import networkx as nx
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

logger = logging.getLogger(__name__)

BATCH_SIZE = 500

class GraphEngine:
    def __init__(self):
        self.uri      = os.getenv("NEO4J_URI")
        self.user     = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")
        self.driver   = None
        # NetworkX fallback for unit tests / offline runs
        self.nx_graph = nx.DiGraph()

    # ── Connection ────────────────────────────────────────────────────────────
    def connect(self) -> bool:
        """Connect to Neo4j Aura. Returns True on success."""
        if not self.uri or not self.password:
            logger.warning("NEO4J_URI or NEO4J_PASSWORD not set — using NetworkX fallback only.")
            return False
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.driver.verify_connectivity()
            logger.info("Connected to Neo4j Aura.")
            return True
        except AuthError:
            logger.error("Neo4j authentication failed. Check NEO4J_USER / NEO4J_PASSWORD.")
            self.driver = None
            return False
        except ServiceUnavailable as e:
            logger.error(f"Neo4j Aura unreachable: {e}")
            self.driver = None
            return False

    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed.")

    def is_connected(self) -> bool:
        return self.driver is not None

    # ── Indexes ───────────────────────────────────────────────────────────────
    def create_indexes(self):
        """
        Idempotent index creation. Run once after connecting.
        Creates indexes on entity_id and entity_type for all node labels.
        """
        if not self.driver:
            return
        cypher = [
            "CREATE INDEX dripe_entity_id   IF NOT EXISTS FOR (n:Entity) ON (n.entity_id)",
            "CREATE INDEX dripe_entity_type IF NOT EXISTS FOR (n:Entity) ON (n.entity_type)",
            "CREATE INDEX dripe_drug_id     IF NOT EXISTS FOR (n:Drug)   ON (n.entity_id)",
            "CREATE INDEX dripe_disease_id  IF NOT EXISTS FOR (n:Disease) ON (n.entity_id)",
        ]
        with self.driver.session(database=self.database) as session:
            for stmt in cypher:
                session.run(stmt)
        logger.info("Neo4j indexes created / verified.")

    # ── Batch Insert ──────────────────────────────────────────────────────────
    def insert_records(self, records: list):
        """
        Batch-inserts a list of RelationshipRecord objects.
        Falls back to NetworkX if Neo4j is unavailable.
        """
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i : i + BATCH_SIZE]
            if self.driver:
                with self.driver.session(database=self.database) as session:
                    session.execute_write(self._write_batch, batch)
            for r in batch:
                self.nx_graph.add_edge(
                    r.source_id, r.target_id,
                    type=r.relationship_type,
                    confidence=r.confidence,
                    source_db=r.source_db
                )

    @staticmethod
    def _write_batch(tx, batch):
        """
        Executes a single batched MERGE transaction for nodes and relationships.
        Uses UNWIND for efficiency.
        """
        params = [
            {
                "source_id":   r.source_id,
                "source_type": r.source_type,
                "target_id":   r.target_id,
                "target_type": r.target_type,
                "rel_type":    r.relationship_type,
                "confidence":  r.confidence,
                "source_db":   r.source_db,
                "pmid":        r.pmid or "",
                "year":        r.evidence_year or 0,
            }
            for r in batch
        ]
        cypher = """
        UNWIND $rows AS row
        MERGE (s:Entity {entity_id: row.source_id})
          ON CREATE SET s.entity_type = row.source_type
        MERGE (t:Entity {entity_id: row.target_id})
          ON CREATE SET t.entity_type = row.target_type
        MERGE (s)-[rel:BIOREL {type: row.rel_type}]->(t)
          ON CREATE SET
            rel.confidence  = row.confidence,
            rel.source_db   = row.source_db,
            rel.pmid        = row.pmid,
            rel.evidence_year = row.year
          ON MATCH SET
            rel.confidence  = CASE WHEN row.confidence > rel.confidence
                                   THEN row.confidence ELSE rel.confidence END
        """
        tx.run(cypher, rows=params)

    # ── Query Helpers ─────────────────────────────────────────────────────────
    def get_node_count(self, label: Optional[str] = None) -> int:
        if not self.driver:
            return self.nx_graph.number_of_nodes()
        q = f"MATCH (n{':' + label if label else ''}) RETURN count(n) AS cnt"
        with self.driver.session(database=self.database) as session:
            result = session.run(q)
            return result.single()["cnt"]

    def get_edge_count(self) -> int:
        if not self.driver:
            return self.nx_graph.number_of_edges()
        with self.driver.session(database=self.database) as session:
            result = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt")
            return result.single()["cnt"]

    def run_cypher(self, cypher: str, params: dict = None):
        """Generic Cypher query. Returns list of dicts."""
        if not self.driver:
            return []
        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, params or {})
            return [dict(record) for record in result]
