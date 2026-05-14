"""
Training script for GAT model on DRIPE knowledge graph.
"""
import torch
import torch.nn.functional as F
import logging
import os
from dotenv import load_dotenv

load_dotenv()

from graph.graph_builder import GraphEngine
from gnn.model import GATModel, LinkPredictor
from gnn.data_loader import load_graph_from_neo4j, create_train_test_split

logger = logging.getLogger(__name__)


def generate_negative_edges(data, num_neg_samples: int = None):
    """
    Generate negative edge samples for link prediction training.
    
    Args:
        data: PyG Data object with positive edges
        num_neg_samples: Number of negative samples (default: same as positive)
    
    Returns:
        Tuple of (pos_edge_index, neg_edge_index)
    """
    num_nodes = data.num_nodes
    num_pos = data.edge_index.shape[1]
    
    if num_neg_samples is None:
        num_neg_samples = num_pos
    
    # Create adjacency set for fast lookup
    edge_set = set()
    for i in range(num_pos):
        src = data.edge_index[0, i].item()
        tgt = data.edge_index[1, i].item()
        edge_set.add((src, tgt))
    
    # Generate negative samples
    neg_src = []
    neg_tgt = []
    
    while len(neg_src) < num_neg_samples:
        src = torch.randint(0, num_nodes, (1,)).item()
        tgt = torch.randint(0, num_nodes, (1,)).item()
        
        if src != tgt and (src, tgt) not in edge_set:
            neg_src.append(src)
            neg_tgt.append(tgt)
    
    neg_edge_index = torch.tensor([neg_src, neg_tgt], dtype=torch.long)
    
    return data.edge_index, neg_edge_index


def train_epoch(model, predictor, data, optimizer, device):
    """Train for one epoch."""
    model.train()
    predictor.train()
    
    # Move data to device
    x = data.x.to(device)
    edge_index = data.edge_index.to(device)
    edge_attr = data.edge_attr.to(device) if data.edge_attr is not None else None
    
    # Generate negative edges
    pos_edge_index, neg_edge_index = generate_negative_edges(data)
    pos_edge_index = pos_edge_index.to(device)
    neg_edge_index = neg_edge_index.to(device)
    
    # Forward pass - get node embeddings
    z = model(x, edge_index, edge_attr)
    
    # Positive predictions
    pos_src = z[pos_edge_index[0]]
    pos_tgt = z[pos_edge_index[1]]
    pos_pred = predictor(pos_src, pos_tgt)
    
    # Negative predictions
    neg_src = z[neg_edge_index[0]]
    neg_tgt = z[neg_edge_index[1]]
    neg_pred = predictor(neg_src, neg_tgt)
    
    # Binary cross-entropy loss
    pos_loss = F.binary_cross_entropy(pos_pred, torch.ones_like(pos_pred))
    neg_loss = F.binary_cross_entropy(neg_pred, torch.zeros_like(neg_pred))
    loss = pos_loss + neg_loss
    
    # Backward pass
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    return loss.item()


@torch.no_grad()
def evaluate(model, predictor, data, device):
    """Evaluate model on test edges."""
    model.eval()
    predictor.eval()
    
    x = data.x.to(device)
    edge_index = data.edge_index.to(device)
    edge_attr = data.edge_attr.to(device) if data.edge_attr is not None else None
    
    # Get embeddings
    z = model(x, edge_index, edge_attr)
    
    # Generate test edges (positive and negative)
    pos_edge_index, neg_edge_index = generate_negative_edges(data)
    pos_edge_index = pos_edge_index.to(device)
    neg_edge_index = neg_edge_index.to(device)
    
    # Positive predictions
    pos_src = z[pos_edge_index[0]]
    pos_tgt = z[pos_edge_index[1]]
    pos_pred = predictor(pos_src, pos_tgt)
    
    # Negative predictions
    neg_src = z[neg_edge_index[0]]
    neg_tgt = z[neg_edge_index[1]]
    neg_pred = predictor(neg_src, neg_tgt)
    
    # Calculate metrics
    pos_correct = (pos_pred > 0.5).float().mean()
    neg_correct = (neg_pred < 0.5).float().mean()
    accuracy = (pos_correct + neg_correct) / 2
    
    # AUC-ROC approximation (can be improved)
    preds = torch.cat([pos_pred, neg_pred]).cpu().numpy()
    labels = torch.cat([torch.ones_like(pos_pred), torch.zeros_like(neg_pred)]).cpu().numpy()
    
    # Simple accuracy-based metric
    return {
        "accuracy": accuracy.item(),
        "pos_correct": pos_correct.item(),
        "neg_correct": neg_correct.item()
    }


def train_model(
    num_epochs: int = 100,
    hidden_dim: int = 64,
    learning_rate: float = 0.01,
    save_path: str = "checkpoints/gat_model.pt"
):
    """
    Main training loop.
    """
    print(f"[I] Starting GAT training for {num_epochs} epochs...")
    
    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[I] Using device: {device}")
    
    # Connect to Neo4j
    engine = GraphEngine()
    if not engine.connect():
        print("[X] Failed to connect to Neo4j. Run docker compose up -d neo4j first.")
        return None
    
    print("[OK] Connected to Neo4j")
    
    # Load graph
    data = load_graph_from_neo4j(engine)
    engine.close()
    
    if data is None:
        print("[X] No graph data found. Run seed_graph.py first.")
        return None
    
    print(f"[OK] Loaded graph: {data.num_nodes} nodes, {data.edge_index.shape[1]} edges")
    
    # Create train/test split
    train_data, test_data = create_train_test_split(data, test_ratio=0.2)
    
    # Initialize models
    in_channels = data.x.shape[1]  # Node feature dimension
    out_channels = hidden_dim
    
    model = GATModel(
        in_channels=in_channels,
        hidden_channels=hidden_dim,
        out_channels=out_channels,
        heads=8
    ).to(device)
    
    predictor = LinkPredictor(in_channels=out_channels).to(device)
    
    # Optimizer
    optimizer = torch.optim.Adam(
        list(model.parameters()) + list(predictor.parameters()),
        lr=learning_rate
    )
    
    # Training loop
    best_accuracy = 0
    
    for epoch in range(num_epochs):
        # Train
        loss = train_epoch(model, predictor, train_data, optimizer, device)
        
        # Evaluate every 10 epochs
        if (epoch + 1) % 10 == 0:
            metrics = evaluate(model, predictor, test_data, device)
            accuracy = metrics["accuracy"]
            
            print(f"Epoch {epoch+1}/{num_epochs} - Loss: {loss:.4f}, Accuracy: {accuracy:.4f}")
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                # Save model
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                torch.save({
                    "model_state": model.state_dict(),
                    "predictor_state": predictor.state_dict(),
                    "in_channels": in_channels,
                    "hidden_dim": hidden_dim,
                    "out_channels": out_channels,
                    "num_nodes": data.num_nodes,
                    "node_mapping": data.node_mapping if hasattr(data, 'node_mapping') else None,
                    "type_mapping": data.type_mapping if hasattr(data, 'type_mapping') else None
                }, save_path)
                print(f"[OK] Model saved (accuracy: {accuracy:.4f})")
    
    print(f"[OK] Training complete. Best accuracy: {best_accuracy:.4f}")
    
    return model, predictor


if __name__ == "__main__":
    train_model()
