"""
PsA enrichment sprint: add missing drug classes (IL-17, IL-12/23, IL-23, PDE4)
to the graph and connect them to PsA via target-disease edges.
"""
import logging, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

from graph.graph_builder import GraphEngine
from ingestion.schemas import RelationshipRecord

# ── Missing target proteins ──────────────────────────────────────────────
TARGETS = [
    {"id": "CHEMBL3390822", "name": "IL17A", "description": "Interleukin-17A"},
    {"id": "CHEMBL3580485", "name": "IL17RA", "description": "Interleukin-17 receptor A"},
    {"id": "CHEMBL3580484", "name": "IL12B", "description": "Interleukin-12 subunit beta (p40)"},
    {"id": "CHEMBL2364154", "name": "IL23A", "description": "Interleukin-23 (p19/p40 heterodimer)"},
    {"id": "CHEMBL275", "name": "PDE4B", "description": "cAMP-specific 3,5-cyclic phosphodiesterase 4B"},
    {"id": "CHEMBL288", "name": "PDE4D", "description": "cAMP-specific 3,5-cyclic phosphodiesterase 4D"},
]

# ── Missing PsA drugs ────────────────────────────────────────────────────
DRUGS = [
    {"id": "PSA_THERAPY_secukinumab", "name": "secukinumab",  "class": "IL-17A inhibitor"},
    {"id": "PSA_THERAPY_ixekizumab",  "name": "ixekizumab",   "class": "IL-17A inhibitor"},
    {"id": "PSA_THERAPY_brodalumab",  "name": "brodalumab",   "class": "IL-17RA inhibitor"},
    {"id": "PSA_THERAPY_ustekinumab", "name": "ustekinumab",  "class": "IL-12/23 inhibitor"},
    {"id": "PSA_THERAPY_guselkumab",  "name": "guselkumab",   "class": "IL-23 inhibitor"},
    {"id": "PSA_THERAPY_risankizumab","name": "risankizumab", "class": "IL-23 inhibitor"},
    {"id": "PSA_THERAPY_tildrakizumab","name":"tildrakizumab","class": "IL-23 inhibitor"},
    {"id": "PSA_THERAPY_apremilast",  "name": "apremilast",   "class": "PDE4 inhibitor"},
]

# ── Drug → Target edges with curated confidence ──────────────────────────
DRUG_TARGET_EDGES = [
    # IL-17A inhibitors
    ("PSA_THERAPY_secukinumab", "CHEMBL3390822", 0.90),
    ("PSA_THERAPY_ixekizumab",  "CHEMBL3390822", 0.90),
    # IL-17RA inhibitor
    ("PSA_THERAPY_brodalumab",  "CHEMBL3580485", 0.90),
    # IL-12/23 inhibitor
    ("PSA_THERAPY_ustekinumab", "CHEMBL3580484", 0.90),
    # IL-23 inhibitors
    ("PSA_THERAPY_guselkumab",  "CHEMBL2364154", 0.90),
    ("PSA_THERAPY_risankizumab","CHEMBL2364154", 0.90),
    ("PSA_THERAPY_tildrakizumab","CHEMBL2364154", 0.90),
    # PDE4 inhibitor (broad PDE4 inhibition)
    ("PSA_THERAPY_apremilast",  "CHEMBL275", 0.85),
    ("PSA_THERAPY_apremilast",  "CHEMBL288", 0.85),
]

# ── Target → Disease (PsA) confidence ────────────────────────────────────
TARGET_DISEASE_EDGES = [
    ("CHEMBL3390822", 0.85),  # IL17A - central in PsA pathogenesis
    ("CHEMBL3580485", 0.80),  # IL17RA - receptor for IL-17A
    ("CHEMBL3580484", 0.75),  # IL12B (p40) - shared IL-12/IL-23 subunit
    ("CHEMBL2364154", 0.80),  # IL23A (p19) - IL-23 specific, Th17 axis
    ("CHEMBL275", 0.60),      # PDE4B - cAMP modulation, anti-inflammatory
    ("CHEMBL288", 0.55),      # PDE4D - cAMP modulation
]

PSA_CUI = "C0395076"

def seed_targets(engine: GraphEngine):
    for t in TARGETS:
        engine.run_cypher(
            "MERGE (n:Entity {entity_id: $eid}) "
            "ON CREATE SET n.entity_type = 'Protein', n.name = $name",
            {"eid": t["id"], "name": t["name"]},
        )
    logger.info(f"Targets created: {len(TARGETS)}")

def seed_drugs(engine: GraphEngine):
    for d in DRUGS:
        engine.run_cypher(
            "MERGE (n:Entity {entity_id: $eid}) "
            "ON CREATE SET n.entity_type = 'Drug', n.name = $name",
            {"eid": d["id"], "name": d["name"]},
        )
    logger.info(f"Drugs created: {len(DRUGS)}")

def seed_drug_target_edges(engine: GraphEngine):
    count = 0
    for drug_id, target_id, conf in DRUG_TARGET_EDGES:
        record = RelationshipRecord(
            source_id=drug_id,
            source_type="Drug",
            target_id=target_id,
            target_type="Protein",
            relationship_type="INTERACTS_WITH",
            confidence=conf,
            source_db="curated",
            evidence_year=2024,
        )
        engine.insert_records([record])
        count += 1
    logger.info(f"Drug->Target edges created: {count}")

def seed_target_disease_edges(engine: GraphEngine):
    count = 0
    for target_id, conf in TARGET_DISEASE_EDGES:
        record = RelationshipRecord(
            source_id=target_id,
            source_type="Protein",
            target_id=PSA_CUI,
            target_type="Disease",
            relationship_type="ASSOCIATED_WITH",
            confidence=conf,
            source_db="curated",
            evidence_year=2024,
        )
        engine.insert_records([record])
        count += 1
    logger.info(f"Target->Disease edges created: {count}")

def verify(engine: GraphEngine):
    logger.info("=== Verification ===")
    r = engine.run_cypher("MATCH (n:Entity) RETURN count(n) AS c")
    r2 = engine.run_cypher("MATCH ()-[r:BIOREL]->() RETURN count(r) AS c")
    logger.info(f"Graph: {r[0]['c']} nodes, {r2[0]['c']} edges")

    # Check new targets
    for t in TARGETS:
        r = engine.run_cypher(
            "MATCH (n:Entity {entity_id: $eid}) RETURN n.entity_type AS t, n.name AS name",
            {"eid": t["id"]},
        )
        if r:
            logger.info(f"  Target {t['id']} ({t['name']}): {r[0]['t']}")
        else:
            logger.warning(f"  Target {t['id']} NOT FOUND")

    # Check new drugs
    for d in DRUGS:
        r = engine.run_cypher(
            "MATCH (n:Entity {entity_id: $eid}) RETURN n.entity_type AS t",
            {"eid": d["id"]},
        )
        if r:
            r2 = engine.run_cypher(
                "MATCH (n:Entity {entity_id: $eid})-[r:BIOREL]->() RETURN r.type AS rel_type, count(r) AS c",
                {"eid": d["id"]},
            )
            edges = "; ".join(f"{rel['rel_type']}: {rel['c']}" for rel in r2) if r2 else "none"
            logger.info(f"  Drug {d['id']} ({d['name']}): edges → {edges}")
        else:
            logger.warning(f"  Drug {d['id']} NOT FOUND")

    # Check PsA disease edges
    r = engine.run_cypher(
        "MATCH (d:Entity {entity_id: $did})<-[r:BIOREL]-(src) "
        "RETURN r.type AS rel_type, count(r) AS c ORDER BY c DESC",
        {"did": PSA_CUI},
    )
    logger.info(f"  PsA ({PSA_CUI}) edges:")
    for row in r:
        logger.info(f"    {row['rel_type']}: {row['c']}")

def main():
    engine = GraphEngine()
    if not engine.connect():
        logger.error("Failed to connect to Neo4j")
        return

    seed_targets(engine)
    seed_drugs(engine)
    seed_drug_target_edges(engine)
    seed_target_disease_edges(engine)
    verify(engine)

    engine.close()

if __name__ == "__main__":
    main()
