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
from ingestion.ra_program.chembl_ra_loader import load_ra_target_interactions
from ingestion.ra_program.clinicaltrials_ra_loader import load_ra_trials, trials_to_records
from reports.graph_stats import print_graph_stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def build_ra_graph():
    """Build the RA-centered subgraph in Neo4j."""
    logger.info("=== DRIPE v2 RA Program Graph Build ===")

    engine = GraphEngine()
    if not engine.connect():
        logger.error("Failed to connect to Neo4j. Is Docker running?")
        return

    logger.info("Step 1: Loading ChEMBL interactions for RA targets...")
    chembl_records = await load_ra_target_interactions(engine)
    if chembl_records:
        engine.insert_records(chembl_records)
        logger.info(f"Inserted {len(chembl_records)} ChEMBL records")

    logger.info("Step 2: Loading RA clinical trials...")
    trials = await load_ra_trials()
    trial_records = trials_to_records(trials)
    if trial_records:
        engine.insert_records(trial_records)
        logger.info(f"Inserted {len(trial_records)} trial records")

    logger.info("Step 3: Printing graph statistics...")
    print_graph_stats(engine)

    engine.close()
    logger.info("=== RA Program Graph Build Complete ===")


if __name__ == "__main__":
    asyncio.run(build_ra_graph())
