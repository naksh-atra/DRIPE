"""
Create Drug→Trial edges for known RA therapies.
Connects each registered RA drug to its clinical trials.
"""
import asyncio, logging, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

from graph.graph_builder import GraphEngine
from ingestion.clinicaltrials_connector import get_clinical_trials
from ingestion.schemas import RelationshipRecord
from config.ra_therapies import get_all, get_chembl_id_map

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_drug_trial_edges():
    engine = GraphEngine()
    if not engine.connect():
        logger.error("Failed to connect to Neo4j")
        return

    therapies = get_all()
    chembl_map = get_chembl_id_map()
    total_edges = 0

    for t in therapies:
        drug_name = t["name"]
        drug_id = t["chembl_id"] if t["chembl_id"] else f"RA_THERAPY_{drug_name}"

        logger.info(f"Fetching trials for {drug_name}...")
        try:
            trials = await get_clinical_trials(drug_name)
        except Exception as e:
            logger.error(f"  Error: {e}")
            continue

        for trial in trials:
            nct_id = trial.get("nct_id", "")
            if not nct_id:
                continue

            # Ensure the Trial node exists
            engine.run_cypher(
                "MERGE (n:Entity {entity_id: $eid}) ON CREATE SET n.entity_type = 'Trial'",
                {"eid": nct_id}
            )

            # Create Drug→Trial edge
            record = RelationshipRecord(
                source_id=drug_id,
                source_type="Drug",
                target_id=nct_id,
                target_type="Trial",
                relationship_type="TRIAL_INVESTIGATES",
                confidence=0.80,
                source_db="clinicaltrials",
                evidence_year=2023,
            )
            engine.insert_records([record])
            total_edges += 1

        logger.info(f"  Added {len(trials)} TRIAL_INVESTIGATES edges for {drug_name}")

    logger.info(f"Created {total_edges} Drug→Trial edges total")

    # Verify
    r = engine.run_cypher("MATCH ()-[rb:BIOREL {type: 'TRIAL_INVESTIGATES'}]->() RETURN count(rb) AS c")
    logger.info(f"Total TRIAL_INVESTIGATES edges in graph: {r[0]['c'] if r else 0}")

    engine.close()


if __name__ == "__main__":
    asyncio.run(create_drug_trial_edges())
