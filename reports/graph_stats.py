"""
Graph statistics reporter for DRIPE.
Prints node/edge counts from Neo4j.
"""
import logging
from graph.graph_builder import GraphEngine

logger = logging.getLogger(__name__)


def print_graph_stats(engine: GraphEngine):
    """Print graph statistics from Neo4j."""
    if not engine.is_connected():
        logger.warning("Not connected to Neo4j")
        return

    node_counts = {}
    edge_counts = {}

    entity_types = ["Drug", "Target", "Disease", "Trial", "Pathway", "AdverseEvent"]
    for etype in entity_types:
        count = engine.get_node_count(f"Entity:{etype}")
        if count > 0:
            node_counts[etype] = count

    edge_types = ["TARGETS", "INDICATES", "TRIAL_INVESTIGATES", "TRIAL_CONDITION",
                  "ASSOCIATED_WITH", "PARTICIPATES_IN", "PATHWAY_DYSREGULATED", "CAUSES"]
    for etype in edge_types:
        cypher = f"MATCH ()-[r:BIOREL {{type: '{etype}'}}]->() RETURN count(r) AS cnt"
        results = engine.run_cypher(cypher)
        if results:
            count = results[0]["cnt"]
            if count > 0:
                edge_counts[etype] = count

    total_nodes = sum(node_counts.values())
    total_edges = sum(edge_counts.values())

    print(f"\n{'='*50}")
    print(f"  DRIPE Graph Statistics")
    print(f"{'='*50}")
    print(f"  Total Nodes: {total_nodes}")
    for etype, count in sorted(node_counts.items()):
        print(f"    {etype}: {count}")
    print(f"  Total Edges: {total_edges}")
    for etype, count in sorted(edge_counts.items()):
        print(f"    {etype}: {count}")
    print(f"{'='*50}\n")
