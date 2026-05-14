"""
RA program graph build script.
Orchestrates ingestion from ChEMBL, ClinicalTrials.gov, and PubMed
into a Neo4j RA-centered subgraph.
"""
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from graph.graph_builder import GraphEngine
from ingestion.schemas import RelationshipRecord
from ingestion.ra_program.chembl_ra_loader import load_ra_target_interactions, RA_TARGETS
from ingestion.ra_program.clinicaltrials_ra_loader import load_ra_trials, trials_to_records
from reports.graph_stats import print_graph_stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Known RA target-disease associations (Target -> RA)
RA_TARGET_CUIS = {
    "CHEMBL1824": "C0003873",    # HER2 -> RA
    "CHEMBL244": "C0003873",     # TNF -> RA
    "CHEMBL2103830": "C0003873", # JAK1 -> RA
    "CHEMBL2146302": "C0003873", # JAK2 -> RA
    "CHEMBL2146303": "C0003873", # JAK3 -> RA
    "CHEMBL4078": "C0003873",    # IL6 -> RA
    "CHEMBL3399910": "C0003873", # IL6R -> RA
    "CHEMBL325": "C0003873",     # IL1B -> RA
    "CHEMBL224": "C0003873",     # COX2 -> RA
    "CHEMBL217": "C0003873",     # COX1 -> RA
    "CHEMBL3712": "C0003873",    # CD20 -> RA
    "CHEMBL3522": "C0003873",    # CTLA4 -> RA
    "CHEMBL258": "C0003873",     # MTOR -> RA
    "CHEMBL1908398": "C0003873", # TYK2 -> RA
}


async def build_ra_graph():
    """Build the RA-centered subgraph in Neo4j."""
    logger.info("=== DRIPE v2 RA Program Graph Build ===")

    engine = GraphEngine()
    if not engine.connect():
        logger.error("Failed to connect to Neo4j.")
        return

    logger.info("Step 1: Loading ChEMBL interactions for RA targets...")
    chembl_records = await load_ra_target_interactions(engine)
    if chembl_records:
        engine.insert_records(chembl_records)
        logger.info(f"Inserted {len(chembl_records)} ChEMBL records")

    logger.info("Step 2: Inserting target-disease associations...")
    target_disease_records = []
    for target_id, disease_cui in RA_TARGET_CUIS.items():
        target_disease_records.append(RelationshipRecord(
            source_id=target_id,
            source_type="Protein",
            target_id=disease_cui,
            target_type="Disease",
            relationship_type="ASSOCIATED_WITH",
            confidence=0.75,
            source_db="curated",
            evidence_year=2023,
        ))
    if target_disease_records:
        engine.insert_records(target_disease_records)
        logger.info(f"Inserted {len(target_disease_records)} target-disease records")

    logger.info("Step 3: Loading RA clinical trials...")
    trials = await load_ra_trials()
    trial_records = trials_to_records(trials)
    if trial_records:
        engine.insert_records(trial_records)
        logger.info(f"Inserted {len(trial_records)} trial records")

    logger.info("Step 4: Printing graph statistics...")
    print_graph_stats(engine)

    engine.close()
    logger.info("=== RA Program Graph Build Complete ===")


if __name__ == "__main__":
    asyncio.run(build_ra_graph())

