import torch
import numpy as np

def augment_sparse_disease_embeddings(
    disease_id: str,
    edge_count: int,
    initial_embedding: torch.Tensor,
    similar_diseases: list,  # List of (well_studied_id, initial_embedding, jaccard_score)
) -> torch.Tensor:
    """
    Computes interpolated embedding for diseases with < 20 edges.
    Weight for own embedding is proportional to edge count (e.g., 5 edges = 25% weight).
    """
    if edge_count >= 20:
        return initial_embedding
        
    own_weight = edge_count / 20.0
    borrowed_weight = (1.0 - own_weight) / len(similar_diseases)
    
    new_embedding = initial_embedding * own_weight
    for _, sim_embedding, _ in similar_diseases:
        new_embedding += sim_embedding * borrowed_weight
        
    return new_embedding
