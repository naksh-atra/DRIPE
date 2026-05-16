"""
Seed adjacent disease nodes (SLE, PsA, Sjogren) with target associations and trial edges.
Creates disease nodes, ASSOCIATED_WITH edges from shared targets, and TRIAL_CONDITION edges.
"""
import asyncio, logging, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

from graph.graph_builder import GraphEngine
from ingestion.clinicaltrials_connector import get_clinical_trials
from ingestion.schemas import RelationshipRecord

DISEASES = [
    {
        "cui": "C0024141",
        "name": "systemic lupus erythematosus",
        "aliases": ["SLE", "lupus"],
        "targets": {
            "CHEMBL244": 0.85,    # TNF
            "CHEMBL3399910": 0.75, # IL6R
            "CHEMBL2103830": 0.75, # JAK1
            "CHEMBL2146302": 0.70, # JAK2
            "CHEMBL3712": 0.80,    # CD20
            "CHEMBL3522": 0.70,    # CTLA4
            "CHEMBL325": 0.65,     # IL1B
            "CHEMBL2027": 0.40,    # DHFR
            "CHEMBL224": 0.55,     # COX2
            "CHEMBL217": 0.50,     # COX1
        },
    },
    {
        "cui": "C0395076",
        "name": "psoriatic arthritis",
        "aliases": ["PsA"],
        "targets": {
            "CHEMBL244": 0.85,    # TNF
            "CHEMBL3399910": 0.75, # IL6R
            "CHEMBL2103830": 0.75, # JAK1
            "CHEMBL2146302": 0.70, # JAK2
            "CHEMBL2146303": 0.55, # JAK3
            "CHEMBL325": 0.65,     # IL1B
            "CHEMBL224": 0.55,     # COX2
            "CHEMBL217": 0.50,     # COX1
        },
    },
    {
        "cui": "C0036075",
        "name": "sjogren syndrome",
        "aliases": ["Sjogren"],
        "targets": {
            "CHEMBL244": 0.85,    # TNF
            "CHEMBL3399910": 0.75, # IL6R
            "CHEMBL2103830": 0.75, # JAK1
            "CHEMBL2146302": 0.70, # JAK2
            "CHEMBL3712": 0.80,    # CD20
            "CHEMBL3522": 0.70,    # CTLA4
        },
    },
]

CT_QUERIES = {
    "C0024141": "systemic+lupus+erythematosus",
    "C0395076": "psoriatic+arthritis",
    "C0036075": "sjogren+syndrome",
}


async def seed_targets(engine: GraphEngine):
    """Create disease nodes and ASSOCIATED_WITH edges from targets."""
    total_target_edges = 0
    for d in DISEASES:
        cui = d["cui"]
        name = d["name"]

        engine.run_cypher(
            "MERGE (n:Entity {entity_id: $eid}) ON CREATE SET n.entity_type = 'Disease', n.name = $name",
            {"eid": cui, "name": name},
        )

        for target_id, confidence in d["targets"].items():
            r = engine.run_cypher(
                "MATCH (p:Entity {entity_id: $tid}) RETURN p.entity_type AS t",
                {"tid": target_id},
            )
            if not r:
                logger.warning(f"  Target {target_id} not found in graph, skipping")
                continue

            record = RelationshipRecord(
                source_id=target_id,
                source_type="Protein",
                target_id=cui,
                target_type="Disease",
                relationship_type="ASSOCIATED_WITH",
                confidence=confidence,
                source_db="literature",
                evidence_year=2024,
            )
            engine.insert_records([record])
            total_target_edges += 1

        logger.info(f"  {name}: {len(d['targets'])} target edges added")

    logger.info(f"Total target-disease edges created: {total_target_edges}")
    return total_target_edges


async def seed_trials(engine: GraphEngine, cui: str, ct_query: str):
    """Fetch trials for a disease and create TRIAL_CONDITION edges."""
    logger.info(f"Fetching trials for {cui}...")
    try:
        trials = await asyncio.wait_for(get_clinical_trials(ct_query, search_field="cond"), timeout=30.0)
    except asyncio.TimeoutError:
        logger.warning(f"  Timeout for {cui}")
        return 0
    except Exception as e:
        logger.warning(f"  Error for {cui}: {e}")
        return 0

    count = 0
    for trial in trials:
        nct_id = trial.get("nct_id", "")
        if not nct_id:
            continue

        engine.run_cypher(
            "MERGE (n:Entity {entity_id: $eid}) ON CREATE SET n.entity_type = 'Trial'",
            {"eid": nct_id},
        )

        record = RelationshipRecord(
            source_id=nct_id,
            source_type="Trial",
            target_id=cui,
            target_type="Disease",
            relationship_type="TRIAL_CONDITION",
            confidence=0.80,
            source_db="clinicaltrials",
            evidence_year=2023,
        )
        engine.insert_records([record])
        count += 1

    logger.info(f"  {cui}: {count} TRIAL_CONDITION edges added")
    return count


async def main():
    engine = GraphEngine()
    if not engine.connect():
        logger.error("Failed to connect to Neo4j")
        return

    # Step 1: Seed disease nodes + target edges
    logger.info("=== Step 1: Target enrichment ===")
    await seed_targets(engine)

    # Verify target edges
    r = engine.run_cypher(
        "MATCH (p:Entity {entity_type: 'Protein'})-[rb:BIOREL {type: 'ASSOCIATED_WITH'}]->(d:Entity {entity_type: 'Disease'}) "
        "RETURN d.entity_id AS disease, count(rb) AS edges ORDER BY disease"
    )
    for row in r:
        logger.info(f"  {row['disease']}: {row['edges']} ASSOCIATED_WITH edges")

    # Step 2: Trial edges for each disease
    logger.info("=== Step 2: Trial enrichment ===")
    for cui, ct_query in CT_QUERIES.items():
        await seed_trials(engine, cui, ct_query)

    # Verify final state
    r = engine.run_cypher("MATCH (n:Entity {entity_type: 'Disease'}) RETURN n.entity_id AS id, n.name AS name ORDER BY id")
    logger.info("=== Final disease nodes ===")
    for row in r:
        rid = engine.run_cypher(
            "MATCH (d:Entity {entity_id: $did})<-[rb:BIOREL]-(src) "
            "RETURN rb.type AS rel_type, count(rb) AS c ORDER BY c DESC",
            {"did": row["id"]},
        )
        rels = "; ".join(f"{rel['rel_type']}: {rel['c']}" for rel in rid)
        logger.info(f"  {row['id']}: {rels}")

    # Total graph state
    r = engine.run_cypher("MATCH (n:Entity) RETURN count(n) AS c")
    r2 = engine.run_cypher("MATCH ()-[r:BIOREL]->() RETURN count(r) AS c")
    logger.info(f"Graph: {r[0]['c']} nodes, {r2[0]['c']} edges")

    engine.close()


if __name__ == "__main__":
    asyncio.run(main())
