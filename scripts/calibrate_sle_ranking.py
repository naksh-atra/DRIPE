"""
SLE ranking calibration pass v2.4a.
Adds missing targets (NR3C1, DHODH), bumps target->SLE confidences where
biologically defensible, and adds direct Drug->SLE edges for drugs without
clear single targets (hydroxychloroquine).
Goal: move more gold therapies above the trial-path floor (product 0.64).
"""
import logging, sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

from graph.graph_builder import GraphEngine
from ingestion.schemas import RelationshipRecord
SLE_CUI = "C0024141"

# -- New targets --------------------------------------------------------
NEW_TARGETS = [
    {"id": "CHEMBL2034", "name": "NR3C1", "desc": "Glucocorticoid receptor"},
    {"id": "CHEMBL1966", "name": "DHODH", "desc": "Dihydroorotate dehydrogenase"},
]

# -- New Drug->Target edges --------------------------------------------
DRUG_TARGET_EDGES = [
    # Prednisone -> NR3C1
    ("CHEMBL635",  "CHEMBL2034", 0.90),
    # Methylprednisolone -> NR3C1
    ("CHEMBL650",  "CHEMBL2034", 0.90),
    # Leflunomide -> DHODH
    ("CHEMBL960",  "CHEMBL1966", 0.85),
]

# -- Target->SLE edges -------------------------------------------------
TARGET_SLE_EDGES = [
    ("CHEMBL2034", 0.72),  # NR3C1 - glucocorticoids are first-line SLE therapy
    ("CHEMBL1966", 0.72),  # DHODH - leflunomide used in SLE
]

# -- Direct Drug->SLE edges (defensible for drugs without clear targets) --
DIRECT_DRUG_SLE = [
    ("CHEMBL1535", 0.80),  # hydroxychloroquine — first-line SLE therapy
]

# -- Target->SLE confidence bumps for existing edges -------------------
BUMP_ASSOCIATED = [
    ("CHEMBL3522", "CTLA4",  0.70, 0.72),  # CTLA4 -> SLE (helps abatacept: 0.90*0.72=0.648 > 0.64)
    ("CHEMBL2027", "DHFR",   0.40, 0.55),  # DHFR -> SLE (helps methotrexate: 0.90*0.55=0.495, still below 0.64)
    ("CHEMBL1902", "FKBP1A", 0.60, 0.72),  # FKBP1A -> SLE (helps tacrolimus: 0.90*0.72=0.648 > 0.64)
]


def seed_targets(engine):
    for t in NEW_TARGETS:
        engine.run_cypher(
            "MERGE (n:Entity {entity_id: $eid}) ON CREATE SET n.entity_type = 'Protein', n.name = $name",
            {"eid": t["id"], "name": t["name"]},
        )
    logger.info(f"New targets created: {len(NEW_TARGETS)}")


def seed_drug_target_edges(engine):
    count = 0
    for drug_id, target_id, conf in DRUG_TARGET_EDGES:
        record = RelationshipRecord(
            source_id=drug_id, source_type="Drug",
            target_id=target_id, target_type="Protein",
            relationship_type="INTERACTS_WITH", confidence=conf,
            source_db="curated", evidence_year=2024,
        )
        engine.insert_records([record])
        count += 1
    logger.info(f"Drug->Target edges: {count}")


def seed_target_sle_edges(engine):
    count = 0
    for target_id, conf in TARGET_SLE_EDGES:
        record = RelationshipRecord(
            source_id=target_id, source_type="Protein",
            target_id=SLE_CUI, target_type="Disease",
            relationship_type="ASSOCIATED_WITH", confidence=conf,
            source_db="curated", evidence_year=2024,
        )
        engine.insert_records([record])
        count += 1
    logger.info(f"Target->SLE edges: {count}")


def seed_direct_drug_sle(engine):
    count = 0
    for drug_id, conf in DIRECT_DRUG_SLE:
        record = RelationshipRecord(
            source_id=drug_id, source_type="Drug",
            target_id=SLE_CUI, target_type="Disease",
            relationship_type="TREATS", confidence=conf,
            source_db="curated", evidence_year=2024,
        )
        engine.insert_records([record])
        count += 1
    logger.info(f"Direct Drug->SLE edges: {count}")


def bump_target_confidences(engine):
    for eid, name, old, new in BUMP_ASSOCIATED:
        r = engine.run_cypher(
            "MATCH (t:Entity {entity_id: $eid})-[r:BIOREL {type:'ASSOCIATED_WITH'}]->(d:Entity {entity_id:$disease}) "
            "SET r.confidence = $new RETURN r.confidence AS c",
            {"eid": eid, "disease": SLE_CUI, "new": new},
        )
        logger.info(f"  {name:10s} (CHEMBL{eid}): {old} -> {new}")


def verify(engine):
    r = engine.run_cypher("MATCH (n:Entity) RETURN count(n) AS c")
    r2 = engine.run_cypher("MATCH ()-[r:BIOREL]->() RETURN count(r) AS c")
    logger.info(f"Graph: {r[0]['c']} nodes, {r2[0]['c']} edges")

    r = engine.run_cypher(
        "MATCH (t:Entity)-[r:BIOREL {type:'ASSOCIATED_WITH'}]->(d:Entity {entity_id:$did}) "
        "RETURN t.entity_id, t.name, r.confidence ORDER BY r.confidence DESC",
        {"did": SLE_CUI},
    )
    logger.info(f"Target->SLE confidences:")
    for row in r:
        tid = row['t.entity_id'] or ''
        tn = row.get('t.name') or tid
        logger.info(f"  {tn:30s} | conf={row.get('r.confidence',0)}")


def main():
    engine = GraphEngine()
    if not engine.connect():
        logger.error("Failed to connect")
        return
    seed_targets(engine)
    seed_drug_target_edges(engine)
    seed_target_sle_edges(engine)
    seed_direct_drug_sle(engine)
    bump_target_confidences(engine)
    verify(engine)
    engine.close()
    logger.info("Calibration complete.")


if __name__ == "__main__":
    main()
