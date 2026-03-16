from neo4j import GraphDatabase
import networkx as nx
import logging
import os

logger = logging.getLogger(__name__)

class GraphEngine:
    def __init__(self, uri=None, user=None, password=None, database=None):
        self.uri = uri or os.getenv("NEO4J_URI")
        self.user = user or os.getenv("NEO4J_USER")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        self.database = database or os.getenv("NEO4J_DATABASE")
        self.driver = None
        
        # NetworkX fallback for local/test use
        self.nx_graph = nx.DiGraph()

    def connect(self):
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.driver.verify_connectivity()
            logger.info("Connected to Neo4j.")
        except Exception as e:
            logger.warning(f"Neo4j connection failed, using NetworkX fallback: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def insert_record(self, record):
        """Batch inserts record into Neo4j and NetworkX."""
        if self.driver:
            with self.driver.session() as session:
                session.execute_write(self._create_node_and_relationship, record)
        
        # Always insert into NetworkX for fallback/testing
        self.nx_graph.add_edge(
            record.source_id, 
            record.target_id, 
            type=record.relationship_type,
            confidence=record.confidence
        )

    @staticmethod
    def _create_node_and_relationship(tx, record):
        query = (
            "MERGE (s:Entity {id: $source_id}) "
            "SET s.type = $source_type "
            "MERGE (t:Entity {id: $target_id}) "
            "SET t.type = $target_type "
            "MERGE (s)-[r:RELATIONSHIP {type: $rel_type}]->(t) "
            "SET r.confidence = $confidence, r.source_db = $source_db"
        )
        tx.run(query, 
               source_id=record.source_id, source_type=record.source_type,
               target_id=record.target_id, target_type=record.target_type,
               rel_type=record.relationship_type, confidence=record.confidence,
               source_db=record.source_db)

    def get_session(self):
        if self.driver:
            return self.driver.session(database=self.database)
        return None
