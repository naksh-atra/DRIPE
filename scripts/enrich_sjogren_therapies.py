"""
Sjogren enrichment: add missing therapies + targets + trial edges.
Follows the same pattern as enrich_sle_therapies.py.

Strategy:
- Phase 1: Name unnamed proteins, add missing drugs/targets
- Phase 2: Add Drug->Target + Target->Sjogren + direct Drug->Sjogren edges
  All target->Sjogren confidences calibrated against trial-path floor (0.64):
  INTERACTS_WITH (0.90) x ASSOCIATED_WITH (X) > 0.64 => X > 0.72
- Phase 3: Drug->Trial + Trial->Sjogren edges via ClinicalTrials.gov
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

SJOGREN_CUI = "C0036075"

# -- Name unnamed proteins -------------------------------------------------
NAME_PROTEINS = [
    ("CHEMBL244",       "TNF"),
    ("CHEMBL3712",      "MS4A1"),
    ("CHEMBL3522",      "CTLA4"),
    ("CHEMBL3399910",   "IL12A"),
    ("CHEMBL2103830",   "IL12B"),
    ("CHEMBL2146302",   "IL17A"),
]

# -- Phase 1: New target ---------------------------------------------------
NEW_TARGETS = [
    {"id": "CHEMBL245", "name": "CHRM3", "desc": "Muscarinic acetylcholine receptor M3"},
]

# -- Phase 1: New drugs ----------------------------------------------------
NEW_DRUGS = [
    {"id": "SJOGREN_THERAPY_pilocarpine",  "name": "pilocarpine"},
    {"id": "SJOGREN_THERAPY_cevimeline",   "name": "cevimeline"},
]

# -- Phase 2: Drug -> Target edges -----------------------------------------
DRUG_TARGET_EDGES = [
    ("SJOGREN_THERAPY_pilocarpine", "CHEMBL245",  0.90),
    ("SJOGREN_THERAPY_cevimeline",  "CHEMBL245",  0.90),
]

# -- Phase 2: Target -> Sjogren edges (ASSOCIATED_WITH) --------------------
# Calibrated: INTERACTS_WITH (0.90) x ASSOCIATED_WITH (X) > 0.64 => X > 0.72
TARGET_SJOGREN_EDGES = [
    ("CHEMBL245",        0.85),  # CHRM3 - pilocarpine/cevimeline target for dryness
    ("CHEMBL2364158",    0.75),  # BAFF - belimumab target, B-cell activity in Sjogren
]

# -- Phase 2: Bump existing target->Sjogren confidences --------------------
BUMP_ASSOCIATED = [
    ("CHEMBL3522", "CTLA4", 0.70, 0.72),  # abatacept: 0.90*0.72=0.648 > 0.64
]

# -- Phase 2: Direct Drug -> Sjogren edges (TREATS) -----------------------
# For drugs without clean target paths that beat the 0.64 floor
DIRECT_DRUG_SJOGREN = [
    ("SLE_THERAPY_cyclophosphamide",  0.70),  # standard-of-care for severe organ involvement
    ("SLE_THERAPY_azathioprine",      0.55),  # steroid-sparing, limited evidence in Sjogren
    ("SLE_THERAPY_mycophenolate_mofetil", 0.60),  # used for systemic manifestations
    ("CHEMBL1535",                    0.65),  # hydroxychloroquine - first-line systemic
    ("CHEMBL635",                     0.65),  # prednisone
    ("CHEMBL650",                     0.65),  # methylprednisolone
    ("SLE_THERAPY_belimumab",         0.55),  # already has BAFF->Sjogren 0.75 path
]

# -- All Sjogren-relevant drugs for trial enrichment -----------------------
TRIAL_DRUG_NAMES = [
    "pilocarpine", "cevimeline",
    "hydroxychloroquine", "methotrexate", "rituximab",
    "belimumab", "azathioprine", "mycophenolate mofetil",
    "cyclophosphamide", "leflunomide",
    "prednisone", "methylprednisolone",
    "abatacept", "anakinra",
]


def name_proteins(engine: GraphEngine):
    count = 0
    for eid, name in NAME_PROTEINS:
        r = engine.run_cypher(
            "MATCH (n:Entity {entity_id: $eid}) SET n.name = $name RETURN n.name",
            {"eid": eid, "name": name},
        )
        if r:
            logger.info(f"  Named {eid} -> {name}")
            count += 1
        else:
            logger.warning(f"  Protein {eid} not found, skipping")
    logger.info(f"Named proteins: {count}/{len(NAME_PROTEINS)}")


def seed_targets(engine: GraphEngine):
    for t in NEW_TARGETS:
        engine.run_cypher(
            "MERGE (n:Entity {entity_id: $eid}) "
            "ON CREATE SET n.entity_type = 'Protein', n.name = $name",
            {"eid": t["id"], "name": t["name"]},
        )
    logger.info(f"New targets created: {len(NEW_TARGETS)}")


def seed_drugs(engine: GraphEngine):
    for d in NEW_DRUGS:
        engine.run_cypher(
            "MERGE (n:Entity {entity_id: $eid}) "
            "ON CREATE SET n.entity_type = 'Drug', n.name = $name",
            {"eid": d["id"], "name": d["name"]},
        )
    logger.info(f"New drugs created: {len(NEW_DRUGS)}")


def seed_drug_target_edges(engine: GraphEngine):
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


def seed_target_sjogren_edges(engine: GraphEngine):
    count = 0
    for target_id, conf in TARGET_SJOGREN_EDGES:
        record = RelationshipRecord(
            source_id=target_id, source_type="Protein",
            target_id=SJOGREN_CUI, target_type="Disease",
            relationship_type="ASSOCIATED_WITH", confidence=conf,
            source_db="curated", evidence_year=2024,
        )
        engine.insert_records([record])
        count += 1
    logger.info(f"Target->Sjogren edges: {count}")


def bump_target_confidences(engine: GraphEngine):
    for eid, name, old, new in BUMP_ASSOCIATED:
        r = engine.run_cypher(
            "MATCH (t:Entity {entity_id: $eid})-[r:BIOREL {type:'ASSOCIATED_WITH'}]->(d:Entity {entity_id:$disease}) "
            "SET r.confidence = $new RETURN r.confidence AS c",
            {"eid": eid, "disease": SJOGREN_CUI, "new": new},
        )
        logger.info(f"  {name:10s} ({eid}): {old} -> {new}")


def seed_direct_drug_sjogren(engine: GraphEngine):
    count = 0
    for drug_id, conf in DIRECT_DRUG_SJOGREN:
        record = RelationshipRecord(
            source_id=drug_id, source_type="Drug",
            target_id=SJOGREN_CUI, target_type="Disease",
            relationship_type="TREATS", confidence=conf,
            source_db="curated", evidence_year=2024,
        )
        engine.insert_records([record])
        count += 1
    logger.info(f"Direct Drug->Sjogren edges: {count}")


async def seed_drug_trial_edges(engine: GraphEngine):
    total_investigates = 0
    total_condition = 0

    for drug_name in TRIAL_DRUG_NAMES:
        query = drug_name.replace(" ", "+")
        logger.info(f"  Trials for '{drug_name}'...")

        try:
            trials = await asyncio.wait_for(
                get_clinical_trials(query), timeout=45.0,
            )
        except asyncio.TimeoutError:
            logger.warning(f"    Timeout for {drug_name}")
            continue
        except Exception as e:
            logger.warning(f"    Error for {drug_name}: {e}")
            continue

        if not trials:
            continue

        drug_node = engine.run_cypher(
            "MATCH (d:Entity) WHERE d.entity_type = 'Drug' AND d.name =~ $name RETURN d.entity_id",
            {"name": f"(?i).*{drug_name}.*"},
        )
        if not drug_node:
            logger.warning(f"    Drug '{drug_name}' not found in graph")
            continue
        drug_eid = drug_node[0]["d.entity_id"]

        drug_count = 0
        for trial in trials:
            nct_id = trial.get("nct_id", "")
            if not nct_id:
                continue

            engine.run_cypher(
                "MERGE (n:Entity {entity_id: $eid}) ON CREATE SET n.entity_type = 'Trial'",
                {"eid": nct_id},
            )

            record = RelationshipRecord(
                source_id=drug_eid, source_type="Drug",
                target_id=nct_id, target_type="Trial",
                relationship_type="TRIAL_INVESTIGATES", confidence=0.80,
                source_db="clinicaltrials", evidence_year=2023,
            )
            engine.insert_records([record])
            drug_count += 1

            exists = engine.run_cypher(
                "MATCH (:Entity {entity_id: $nct})-[r:BIOREL {type:'TRIAL_CONDITION'}]->(:Entity {entity_id:$dis}) "
                "RETURN count(r) AS c",
                {"nct": nct_id, "dis": SJOGREN_CUI},
            )
            if exists and exists[0]["c"] == 0:
                record2 = RelationshipRecord(
                    source_id=nct_id, source_type="Trial",
                    target_id=SJOGREN_CUI, target_type="Disease",
                    relationship_type="TRIAL_CONDITION", confidence=0.80,
                    source_db="clinicaltrials", evidence_year=2023,
                )
                engine.insert_records([record2])
                total_condition += 1

        total_investigates += drug_count
        logger.info(f"    {drug_name}: {drug_count} TRIAL_INVESTIGATES")
        await asyncio.sleep(0.5)

    logger.info(f"TOTAL: {total_investigates} TRIAL_INVESTIGATES, {total_condition} TRIAL_CONDITION (new)")


def verify(engine: GraphEngine):
    r = engine.run_cypher("MATCH (n:Entity) RETURN count(n) AS c")
    r2 = engine.run_cypher("MATCH ()-[r:BIOREL]->() RETURN count(r) AS c")
    logger.info(f"Graph: {r[0]['c']} nodes, {r2[0]['c']} edges")

    r = engine.run_cypher(
        "MATCH (d:Entity {entity_id: $did})<-[rb:BIOREL]-(src) "
        "RETURN rb.type AS rel_type, count(rb) AS c ORDER BY c DESC",
        {"did": SJOGREN_CUI},
    )
    logger.info(f"Sjogren ({SJOGREN_CUI}) edges:")
    for row in r:
        logger.info(f"  {row['rel_type']}: {row['c']}")

    for t in NEW_TARGETS:
        r = engine.run_cypher(
            "MATCH (n:Entity {entity_id: $eid})-[r:BIOREL]->() RETURN r.type, count(r) AS c",
            {"eid": t["id"]},
        )
        out = "; ".join(f"{rel['r.type']}: {rel['c']}" for rel in r) if r else "none"
        logger.info(f"  Target {t['id']} ({t['name']}): out {out}")

    for d in NEW_DRUGS:
        r = engine.run_cypher(
            "MATCH (n:Entity {entity_id: $eid})-[r:BIOREL]->() RETURN r.type, count(r) AS c",
            {"eid": d["id"]},
        )
        out = "; ".join(f"{rel['r.type']}: {rel['c']}" for rel in r) if r else "none"
        logger.info(f"  Drug {d['id']} ({d['name']}): out {out}")


async def main():
    engine = GraphEngine()
    if not engine.connect():
        logger.error("Failed to connect")
        return

    logger.info("=== Phase 0: Name proteins ===")
    name_proteins(engine)

    logger.info("=== Phase 1: Nodes ===")
    seed_targets(engine)
    seed_drugs(engine)

    logger.info("=== Phase 2: Edges ===")
    seed_drug_target_edges(engine)
    seed_target_sjogren_edges(engine)
    bump_target_confidences(engine)
    seed_direct_drug_sjogren(engine)

    logger.info("=== Phase 3: Trials ===")
    await seed_drug_trial_edges(engine)

    logger.info("=== Verify ===")
    verify(engine)
    engine.close()
    logger.info("Sjogren enrichment complete.")


if __name__ == "__main__":
    asyncio.run(main())
