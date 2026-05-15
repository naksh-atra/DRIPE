"""
Insert known RA therapies into Neo4j graph.
Adds Drug nodes with names and Drug→Target edges for approved therapies.
"""
import logging, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

from graph.graph_builder import GraphEngine
from ingestion.schemas import RelationshipRecord
from config.ra_therapies import get_all

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest():
    engine = GraphEngine()
    if not engine.connect():
        logger.error("Failed to connect to Neo4j")
        return

    therapies = get_all()
    logger.info(f"Ingesting {len(therapies)} known RA therapies")

    for t in therapies:
        drug_id = t["chembl_id"] if t["chembl_id"] else f"RA_THERAPY_{t['name']}"
        drug_name = t["name"]

        # Create or update Drug node with name property
        engine.run_cypher(
            "MERGE (n:Entity {entity_id: $eid}) ON CREATE SET n.entity_type = 'Drug', n.name = $name "
            "ON MATCH SET n.name = $name",
            {"eid": drug_id, "name": drug_name}
        )
        logger.info(f"  Drug node: {drug_name} ({drug_id})")

        # Create Drug→Target edges for known targets
        for target in t["targets"]:
            # Check if target exists in graph
            exists = engine.run_cypher(
                "MATCH (n:Entity {entity_id: $eid}) RETURN count(n) AS c",
                {"eid": target["id"]}
            )
            if not exists or exists[0]["c"] == 0:
                # Create the target node if it doesn't exist
                engine.run_cypher(
                    "MERGE (n:Entity {entity_id: $eid}) ON CREATE SET n.entity_type = 'Protein', n.name = $name",
                    {"eid": target["id"], "name": target["name"]}
                )
                logger.info(f"  Created missing target node: {target['name']} ({target['id']})")

            # Create Drug→Target edge
            record = RelationshipRecord(
                source_id=drug_id,
                source_type="Drug",
                target_id=target["id"],
                target_type="Protein",
                relationship_type="INTERACTS_WITH",
                confidence=0.90,
                source_db="curated_ra_therapy",
                evidence_year=2023,
            )
            engine.insert_records([record])
            logger.info(f"  Edge: {drug_name} -> {target['name']}")

    # Print summary
    drug_count = engine.run_cypher("MATCH (n:Entity {entity_type: 'Drug'}) RETURN count(n) AS c")[0]["c"]
    edge_count = engine.get_edge_count()
    logger.info(f"Total Drug nodes: {drug_count}")
    logger.info(f"Total edges: {edge_count}")

    engine.close()
    logger.info("Ingestion complete")


if __name__ == "__main__":
    ingest()
