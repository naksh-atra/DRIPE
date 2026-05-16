"""Finish apremilast + tildrakizumab Drug→Trial edges."""
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
REMAINING = [
    {"name": "tildrakizumab", "id": "PSA_THERAPY_tildrakizumab"},
    {"name": "apremilast",    "id": "PSA_THERAPY_apremilast"},
]

async def finish():
    engine = GraphEngine()
    engine.connect()

    for drug in REMAINING:
        name = drug["name"]
        drug_id = drug["id"]

        existing = engine.run_cypher(
            "MATCH (n:Entity {entity_id: $eid})-[r:BIOREL {type: 'TRIAL_INVESTIGATES'}]->() RETURN count(r) AS c",
            {"eid": drug_id}
        )
        already = existing[0]["c"] if existing else 0
        if already >= 50:
            logger.info(f"{name}: already has {already} edges, skipping")
            continue

        logger.info(f"Fetching trials for {name} (has {already} already)...")
        try:
            trials = await asyncio.wait_for(get_clinical_trials(name, search_field="intr"), timeout=30.0)
        except asyncio.TimeoutError:
            logger.warning(f"  Timeout for {name}")
            continue
        except Exception as e:
            logger.error(f"  Error: {e}")
            continue

        count = 0
        for trial in trials:
            nct_id = trial.get("nct_id", "")
            if not nct_id:
                continue

            engine.run_cypher(
                "MERGE (n:Entity {entity_id: $eid}) ON CREATE SET n.entity_type = 'Trial'",
                {"eid": nct_id}
            )

            # Skip if edge already exists
            existing_edge = engine.run_cypher(
                "MATCH (s:Entity {entity_id: $sid})-[r:BIOREL {type: 'TRIAL_INVESTIGATES'}]->(t:Entity {entity_id: $tid}) RETURN count(r) AS c",
                {"sid": drug_id, "tid": nct_id}
            )
            if existing_edge and existing_edge[0]["c"] > 0:
                continue

            engine.insert_records([RelationshipRecord(
                source_id=drug_id, source_type="Drug",
                target_id=nct_id, target_type="Trial",
                relationship_type="TRIAL_INVESTIGATES",
                confidence=0.85, source_db="clinicaltrials", evidence_year=2024,
            )])
            count += 1

            # Check/add TRIAL_CONDITION
            has_cond = engine.run_cypher(
                "MATCH (t:Entity {entity_id: $tid})-[r:BIOREL {type: 'TRIAL_CONDITION'}]->(d:Entity {entity_id: $did}) RETURN count(r) AS c",
                {"tid": nct_id, "did": PSA_CUI}
            )
            if not has_cond or has_cond[0]["c"] == 0:
                engine.insert_records([RelationshipRecord(
                    source_id=nct_id, source_type="Trial",
                    target_id=PSA_CUI, target_type="Disease",
                    relationship_type="TRIAL_CONDITION",
                    confidence=0.80, source_db="clinicaltrials", evidence_year=2024,
                )])

        logger.info(f"  {name}: added {count} new TRIAL_INVESTIGATES edges")

    r = engine.run_cypher("MATCH (n:Entity) RETURN count(n) AS c")
    r2 = engine.run_cypher("MATCH ()-[r:BIOREL]->() RETURN count(r) AS c")
    r3 = engine.run_cypher("MATCH ()-[r:BIOREL {type: 'TRIAL_INVESTIGATES'}]->() RETURN count(r) AS c")
    r4 = engine.run_cypher("MATCH ()-[r:BIOREL {type: 'TRIAL_CONDITION'}]->() RETURN count(r) AS c")
    logger.info(f"Graph: {r[0]['c']} nodes, {r2[0]['c']} edges | TRIAL_INVESTIGATES: {r3[0]['c']} | TRIAL_CONDITION: {r4[0]['c']}")

    engine.close()

asyncio.run(finish())
