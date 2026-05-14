"""
Tests the ChEMBL connector and optionally pushes a small set to Neo4j.
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
sys.path.insert(0, os.path.dirname(__file__))

from ingestion.chembl_connector import get_chembl_activity
from graph.graph_builder import GraphEngine

async def main():
    # Test target: HER2 (ERBB2) Target ChEMBL ID: CHEMBL1824
    target_id = "CHEMBL1824"
    print(f"--- Testing ChEMBL Ingestion for HER2 ({target_id}) ---")
    
    records = await get_chembl_activity(target_id)
    
    if not records:
        print("No records found (or error).")
        return

    print(f"Fetched {len(records)} high-potency relationships.")
    print("Sample record:", records[0])

    # Optional: Push to Neo4j Aura if connected
    engine = GraphEngine()
    if engine.connect():
        print("Connected to Neo4j. Pushing sample batch...")
        engine.insert_records(records[:50]) # Push only first 50 for testing
        print("✅ Sample batch inserted.")
        engine.close()
    else:
        print("Neo4j connection skipped.")

if __name__ == "__main__":
    asyncio.run(main())
