"""
Create Drug→Trial edges for the 8 newly added PsA therapies.
Also creates TRIAL_CONDITION edges for any new trials found.
"""
import asyncio, logging, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

from graph.graph_builder import GraphEngine
from ingestion.clinicaltrials_connector import get_clinical_trials
from ingestion.schemas import RelationshipRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PSA_CUI = "C0395076"
PSA_QUERY = "psoriatic+arthritis"

PSA_DRUGS = [
    {"name": "secukinumab",  "id": "PSA_THERAPY_secukinumab"},
    {"name": "ixekizumab",   "id": "PSA_THERAPY_ixekizumab"},
    {"name": "brodalumab",   "id": "PSA_THERAPY_brodalumab"},
    {"name": "ustekinumab",  "id": "PSA_THERAPY_ustekinumab"},
    {"name": "guselkumab",   "id": "PSA_THERAPY_guselkumab"},
    {"name": "risankizumab", "id": "PSA_THERAPY_risankizumab"},
    {"name": "tildrakizumab","id": "PSA_THERAPY_tildrakizumab"},
    {"name": "apremilast",   "id": "PSA_THERAPY_apremilast"},
]

async def create_trial_edges():
    engine = GraphEngine()
    if not engine.connect():
        logger.error("Failed to connect to Neo4j")
        return

    total_investigates = 0
    total_conditions = 0
    total_new_trials = 0

    for drug in PSA_DRUGS:
        name = drug["name"]
        drug_id = drug["id"]

        logger.info(f"Fetching trials for {name}...")
        try:
            trials = await asyncio.wait_for(get_clinical_trials(name, search_field="intr"), timeout=30.0)
        except asyncio.TimeoutError:
            logger.warning(f"  Timeout for {name}")
            continue
        except Exception as e:
            logger.error(f"  Error for {name}: {e}")
            continue

        for trial in trials:
            nct_id = trial.get("nct_id", "")
            if not nct_id:
                continue

            # Ensure Trial node exists
            engine.run_cypher(
                "MERGE (n:Entity {entity_id: $eid}) ON CREATE SET n.entity_type = 'Trial'",
                {"eid": nct_id}
            )

            # Check if it's a new trial (no existing TRIAL_CONDITION to PsA)
            existing = engine.run_cypher(
                "MATCH (t:Entity {entity_id: $tid})-[r:BIOREL {type: 'TRIAL_CONDITION'}]->(d:Entity {entity_id: $did}) RETURN count(r) AS c",
                {"tid": nct_id, "did": PSA_CUI}
            )
            is_new = not existing or existing[0]["c"] == 0

            # Create Drug→Trial edge
            record = RelationshipRecord(
                source_id=drug_id,
                source_type="Drug",
                target_id=nct_id,
                target_type="Trial",
                relationship_type="TRIAL_INVESTIGATES",
                confidence=0.85,
                source_db="clinicaltrials",
                evidence_year=2024,
            )
            engine.insert_records([record])
            total_investigates += 1

            # Create Trial→PsA edge if new
            if is_new:
                cond_record = RelationshipRecord(
                    source_id=nct_id,
                    source_type="Trial",
                    target_id=PSA_CUI,
                    target_type="Disease",
                    relationship_type="TRIAL_CONDITION",
                    confidence=0.80,
                    source_db="clinicaltrials",
                    evidence_year=2024,
                )
                engine.insert_records([cond_record])
                total_conditions += 1
                total_new_trials += 1

        logger.info(f"  {name}: {len(trials)} trials, {len(trials)} TRIAL_INVESTIGATES edges")

    logger.info(f"\n=== Summary ===")
    logger.info(f"TRIAL_INVESTIGATES edges created: {total_investigates}")
    logger.info(f"New TRIAL_CONDITION edges created: {total_conditions}")
    logger.info(f"New trials linked to PsA: {total_new_trials}")

    r = engine.run_cypher("MATCH ()-[r:BIOREL {type: 'TRIAL_INVESTIGATES'}]->() RETURN count(r) AS c")
    r2 = engine.run_cypher("MATCH ()-[r:BIOREL {type: 'TRIAL_CONDITION'}]->() RETURN count(r) AS c")
    r3 = engine.run_cypher("MATCH (n:Entity) RETURN count(n) AS c_nodes")
    r4 = engine.run_cypher("MATCH ()-[r:BIOREL]->() RETURN count(r) AS c_edges")
    logger.info(f"Graph state: {r3[0]['c_nodes']} nodes, {r4[0]['c_edges']} edges")
    logger.info(f"  TRIAL_INVESTIGATES: {r[0]['c']}")
    logger.info(f"  TRIAL_CONDITION: {r2[0]['c']}")

    engine.close()

if __name__ == "__main__":
    asyncio.run(create_trial_edges())
