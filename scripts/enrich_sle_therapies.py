"""
SLE enrichment v2.4: add missing SLE therapies + targets + trial edges.
Three phases: (1) target+drug nodes, (2) target->SLE and drug->target edges,
(3) trial enrichment for ALL SLE therapies.
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

SLE_CUI = "C0024141"

# Phase 1: New targets
NEW_TARGETS = [
    {"id": "CHEMBL2364158", "name": "BAFF",  "desc": "B-cell activating factor"},
    {"id": "CHEMBL1887",    "name": "IFNAR1","desc": "Interferon alpha/beta receptor 1"},
    {"id": "CHEMBL1822",    "name": "IMPDH1","desc": "Inosine-5'-monophosphate dehydrogenase 1"},
    {"id": "CHEMBL1902",    "name": "FKBP1A","desc": "Peptidyl-prolyl cis-trans isomerase FKBP1A"},
]

# Phase 1: New drugs
NEW_DRUGS = [
    {"id": "SLE_THERAPY_belimumab",           "name": "belimumab"},
    {"id": "SLE_THERAPY_mycophenolate_mofetil","name": "mycophenolate mofetil"},
    {"id": "SLE_THERAPY_cyclophosphamide",     "name": "cyclophosphamide"},
    {"id": "SLE_THERAPY_azathioprine",         "name": "azathioprine"},
    {"id": "SLE_THERAPY_anifrolumab",          "name": "anifrolumab"},
    {"id": "SLE_THERAPY_tacrolimus",           "name": "tacrolimus"},
]

# Phase 2: Drug -> Target edges
DRUG_TARGET_EDGES = [
    ("SLE_THERAPY_belimumab",            "CHEMBL2364158", 0.90),
    ("SLE_THERAPY_mycophenolate_mofetil", "CHEMBL1822",   0.85),
    ("SLE_THERAPY_anifrolumab",          "CHEMBL1887",    0.90),
    ("SLE_THERAPY_tacrolimus",           "CHEMBL1902",    0.85),
]

# Phase 2: Target -> SLE edges
TARGET_SLE_EDGES = [
    ("CHEMBL2364158", 0.80),  # BAFF - B-cell survival in SLE (belimumab target, approved)
    ("CHEMBL1887",    0.85),  # IFNAR1 - type I interferon axis (anifrolumab target, approved)
    ("CHEMBL1822",    0.75),  # IMPDH1 - lymphocyte proliferation (mycophenolate is standard-of-care)
    ("CHEMBL1902",    0.60),  # FKBP1A - calcineurin pathway (tacrolimus in lupus nephritis)
]

# Phase 2: Direct Drug -> SLE edges (no specific protein target)
DIRECT_DRUG_SLE_EDGES = [
    ("SLE_THERAPY_cyclophosphamide", 0.80),  # standard-of-care lupus nephritis
    ("SLE_THERAPY_azathioprine",     0.70),  # steroid-sparing agent
]

# All SLE drugs for trial enrichment (name as used in graph)
TRIAL_DRUG_NAMES = [
    "belimumab", "mycophenolate mofetil", "cyclophosphamide",
    "azathioprine", "anifrolumab", "tacrolimus",
    "hydroxychloroquine", "methotrexate", "rituximab",
    "prednisone", "methylprednisolone", "leflunomide", "abatacept",
]


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


def seed_target_sle_edges(engine: GraphEngine):
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


def seed_direct_drug_sle_edges(engine: GraphEngine):
    count = 0
    for drug_id, conf in DIRECT_DRUG_SLE_EDGES:
        record = RelationshipRecord(
            source_id=drug_id, source_type="Drug",
            target_id=SLE_CUI, target_type="Disease",
            relationship_type="TREATS", confidence=conf,
            source_db="curated", evidence_year=2024,
        )
        engine.insert_records([record])
        count += 1
    logger.info(f"Direct Drug->SLE edges: {count}")


async def seed_drug_trial_edges(engine: GraphEngine):
    """For each SLE drug: fetch trials, create TRIAL_INVESTIGATES + TRIAL_CONDITION->SLE."""
    total_investigates = 0
    total_condition = 0

    for drug_name in TRIAL_DRUG_NAMES:
        query = drug_name.replace(" ", "+")
        logger.info(f"  Trials for '{drug_name}'...")

        try:
            trials = await asyncio.wait_for(
                get_clinical_trials(query, search_field="intr"), timeout=45.0,
            )
        except asyncio.TimeoutError:
            logger.warning(f"    Timeout for {drug_name}")
            continue
        except Exception as e:
            logger.warning(f"    Error for {drug_name}: {e}")
            continue

        if not trials:
            continue

        # Find drug node entity_id
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

            # Ensure trial node exists
            engine.run_cypher(
                "MERGE (n:Entity {entity_id: $eid}) ON CREATE SET n.entity_type = 'Trial'",
                {"eid": nct_id},
            )

            # TRIAL_INVESTIGATES (Drug -> Trial)
            record = RelationshipRecord(
                source_id=drug_eid, source_type="Drug",
                target_id=nct_id, target_type="Trial",
                relationship_type="TRIAL_INVESTIGATES", confidence=0.80,
                source_db="clinicaltrials", evidence_year=2023,
            )
            engine.insert_records([record])
            drug_count += 1

            # TRIAL_CONDITION (Trial -> SLE) if not already exists
            exists = engine.run_cypher(
                "MATCH (:Entity {entity_id: $nct})-[r:BIOREL {type:'TRIAL_CONDITION'}]->(:Entity {entity_id:$dis}) "
                "RETURN count(r) AS c",
                {"nct": nct_id, "dis": SLE_CUI},
            )
            if exists and exists[0]["c"] == 0:
                record2 = RelationshipRecord(
                    source_id=nct_id, source_type="Trial",
                    target_id=SLE_CUI, target_type="Disease",
                    relationship_type="TRIAL_CONDITION", confidence=0.80,
                    source_db="clinicaltrials", evidence_year=2023,
                )
                engine.insert_records([record2])
                total_condition += 1

        total_investigates += drug_count
        logger.info(f"    {drug_name}: {drug_count} TRIAL_INVESTIGATES")
        await asyncio.sleep(0.5)  # rate-limit politeness

    logger.info(f"TOTAL: {total_investigates} TRIAL_INVESTIGATES, {total_condition} TRIAL_CONDITION (new)")


def verify(engine: GraphEngine):
    r = engine.run_cypher("MATCH (n:Entity) RETURN count(n) AS c")
    r2 = engine.run_cypher("MATCH ()-[r:BIOREL]->() RETURN count(r) AS c")
    logger.info(f"Graph: {r[0]['c']} nodes, {r2[0]['c']} edges")

    r = engine.run_cypher(
        "MATCH (d:Entity {entity_id: $did})<-[rb:BIOREL]-(src) "
        "RETURN rb.type AS rel_type, count(rb) AS c ORDER BY c DESC",
        {"did": SLE_CUI},
    )
    logger.info(f"SLE ({SLE_CUI}) edges:")
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

    logger.info("=== Phase 1: Nodes ===")
    seed_targets(engine)
    seed_drugs(engine)

    logger.info("=== Phase 2: Edges ===")
    seed_drug_target_edges(engine)
    seed_target_sle_edges(engine)
    seed_direct_drug_sle_edges(engine)

    logger.info("=== Phase 3: Trials ===")
    await seed_drug_trial_edges(engine)

    logger.info("=== Verify ===")
    verify(engine)
    engine.close()
    logger.info("SLE enrichment complete.")


if __name__ == "__main__":
    asyncio.run(main())
