"""Check what paths exist in Neo4j for RA."""
from dotenv import load_dotenv
load_dotenv()
from graph.graph_builder import GraphEngine

g = GraphEngine()
g.connect()

# Check what edges go to/from the RA disease node
print("=== Edges to/from RA disease ===")
r = g.run_cypher("MATCH (n)-[rb:BIOREL]->(m:Entity {entity_id: 'C0003873'}) RETURN n.entity_type AS src_type, n.entity_id AS src_id, rb.type AS rel_type LIMIT 20")
for row in r:
    print(f"  {row['src_type']} {row['src_id']} --[{row['rel_type']}]--> RA")

# Check what edges from drugs go to
print("\n=== Drug outgoing edges ===")
r = g.run_cypher("MATCH (n:Entity {entity_type: 'Drug'})-[rb:BIOREL]->(m) RETURN n.entity_id AS drug, m.entity_type AS tgt_type, rb.type AS rel_type LIMIT 10")
for row in r:
    print(f"  {row['drug']} --[{row['rel_type']}]--> {row['tgt_type']}")

# Check what edges from targets go to
print("\n=== Target outgoing edges ===")
r = g.run_cypher("MATCH (n:Entity {entity_type: 'Protein'})-[rb:BIOREL]->(m) RETURN n.entity_id AS tgt, m.entity_type AS tgt_type, rb.type AS rel_type LIMIT 10")
for row in r:
    print(f"  {row['tgt']} --[{row['rel_type']}]--> {row['tgt_type']}")

g.close()
