"""
Loads graph data from Neo4j into PyTorch Geometric format.
"""
import torch
from torch_geometric.data import Data
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def load_graph_from_neo4j(graph_engine, max_nodes: int = 10000) -> Optional[Data]:
    """
    Loads nodes and edges from Neo4j into a PyTorch Geometric Data object.
    
    Args:
        graph_engine: GraphEngine instance (connected to Neo4j)
        max_nodes: Maximum nodes to load (for memory management)
    
    Returns:
        torch_geometric.data.Data object or None if no data
    """
    if not graph_engine.is_connected():
        logger.error("Not connected to Neo4j. Cannot load graph.")
        return None
    
    # Fetch nodes with types
    node_query = """
    MATCH (n:Entity)
    RETURN n.entity_id AS id, n.entity_type AS type
    LIMIT $max_nodes
    """
    
    with graph_engine.driver.session(database=graph_engine.database) as session:
        result = session.run(node_query, max_nodes=max_nodes)
        nodes = [(record["id"], record["type"]) for record in result]
    
    if not nodes:
        logger.warning("No nodes found in Neo4j.")
        return None
    
    # Create node ID mapping
    node_id_to_idx = {node[0]: idx for idx, node in enumerate(nodes)}
    
    # Fetch edges
    edge_query = """
    MATCH (s:Entity)-[r:BIOREL]->(t:Entity)
    WHERE s.entity_id IN $node_ids AND t.entity_id IN $node_ids
    RETURN s.entity_id AS source, t.entity_id AS target, r.type AS type, r.confidence AS confidence
    """
    
    node_ids = [n[0] for n in nodes]
    
    with graph_engine.driver.session(database=graph_engine.database) as session:
        result = session.run(edge_query, node_ids=node_ids)
        edges = [(record["source"], record["target"], record["type"], record["confidence"]) 
                 for record in result]
    
    if not edges:
        logger.warning("No edges found. Creating graph with nodes only.")
        # Create empty edge tensor
        edge_index = torch.zeros((2, 0), dtype=torch.long)
        edge_attr = torch.zeros((0, 1), dtype=torch.float)
    else:
        # Build edge index and attributes
        src_indices = []
        tgt_indices = []
        confidences = []
        
        for src, tgt, rel_type, conf in edges:
            if src in node_id_to_idx and tgt in node_id_to_idx:
                src_indices.append(node_id_to_idx[src])
                tgt_indices.append(node_id_to_idx[tgt])
                confidences.append(conf or 0.5)
        
        edge_index = torch.tensor([src_indices, tgt_indices], dtype=torch.long)
        edge_attr = torch.tensor(confidences, dtype=torch.float).unsqueeze(1)
    
    # Create node features (one-hot encoding by entity type)
    unique_types = list(set(n[1] for n in nodes))
    type_to_idx = {t: i for i, t in enumerate(unique_types)}
    
    num_nodes = len(nodes)
    num_types = len(unique_types)
    
    # One-hot encoding
    x = torch.zeros(num_nodes, num_types)
    for idx, (_, node_type) in enumerate(nodes):
        type_idx = type_to_idx[node_type]
        x[idx, type_idx] = 1.0
    
    # Create node ID mapping for later use
    node_mapping = {idx: node_id for idx, (node_id, _) in enumerate(nodes)}
    
    # Create PyG Data object
    data = Data(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attr,
        num_nodes=num_nodes
    )
    
    # Store metadata
    data.node_mapping = node_mapping
    data.node_id_to_idx = node_id_to_idx
    data.type_mapping = type_to_idx
    data.node_types = [n[1] for n in nodes]
    data.node_ids = [n[0] for n in nodes]
    
    logger.info(f"Loaded graph: {num_nodes} nodes, {edge_index.shape[1]} edges, {num_types} entity types")
    
    return data


def create_train_test_split(data: Data, test_ratio: float = 0.2) -> Tuple[Data, Data]:
    """
    Splits edges into train/test sets for link prediction.
    
    Args:
        data: PyG Data object
        test_ratio: Fraction of edges to use for testing
    
    Returns:
        Tuple of (train_data, test_data)
    """
    num_edges = data.edge_index.shape[1]
    
    if num_edges == 0:
        logger.warning("No edges to split.")
        return data, data
    
    # Shuffle edge indices
    perm = torch.randperm(num_edges)
    
    # Split
    test_size = int(num_edges * test_ratio)
    test_mask = perm[:test_size]
    train_mask = perm[test_size:]
    
    # Create train data
    train_data = data.clone()
    train_data.edge_index = data.edge_index[:, train_mask]
    train_data.edge_attr = data.edge_attr[train_mask] if data.edge_attr is not None else None
    
    # Create test data (just for evaluation)
    test_data = data.clone()
    test_data.edge_index = data.edge_index[:, test_mask]
    test_data.edge_attr = data.edge_attr[test_mask] if data.edge_attr is not None else None
    
    logger.info(f"Train edges: {len(train_mask)}, Test edges: {len(test_mask)}")
    
    return train_data, test_data


def print_graph_stats(data: Data):
    """Prints graph statistics."""
    print(f"Nodes: {data.num_nodes}")
    print(f"Edges: {data.edge_index.shape[1]}")
    print(f"Node features dim: {data.x.shape[1]}")
    print(f"Entity types: {len(set(data.node_types)) if hasattr(data, 'node_types') else 'N/A'}")
    if hasattr(data, 'node_types'):
        type_counts = {}
        for t in data.node_types:
            type_counts[t] = type_counts.get(t, 0) + 1
        print("Type distribution:")
        for t, count in sorted(type_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"  {t}: {count}")
