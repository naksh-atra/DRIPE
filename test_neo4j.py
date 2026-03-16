"""
Run this once to verify Neo4j Aura connectivity and create indexes.
Usage:  dripenv\Scripts\python.exe test_neo4j.py
"""
import os
import sys
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

sys.path.insert(0, os.path.dirname(__file__))
from graph.graph_builder import GraphEngine

def main():
    engine = GraphEngine()
    print(f"Connecting to: {engine.uri}")
    
    ok = engine.connect()
    if not ok:
        print("❌ Connection failed. Check NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in .env")
        sys.exit(1)
    
    print("✅ Connected to Neo4j Aura!")
    
    # Create indexes
    engine.create_indexes()
    print("✅ Indexes verified.")
    
    # Node/edge counts
    nodes = engine.get_node_count()
    edges = engine.get_edge_count()
    print(f"📊 Current graph state — Nodes: {nodes}, Edges: {edges}")
    
    # Quick connectivity test
    results = engine.run_cypher("RETURN 'DRIPE Neo4j Aura connection OK' AS status")
    print(f"🔗 {results[0]['status']}")
    
    engine.close()
    print("Done.")

if __name__ == "__main__":
    main()
