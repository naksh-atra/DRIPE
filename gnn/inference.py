"""
Inference module for GNN link prediction.
Integrates trained GAT model with DRIPE API.
"""
import torch
import os
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "..", "checkpoints", "gat_model.pt")


class GNNPredictor:
    """Wrapper for GAT model inference."""
    
    def __init__(self, checkpoint_path: str = None):
        self.checkpoint_path = checkpoint_path or CHECKPOINT_PATH
        self.model = None
        self.predictor = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.node_mapping = None
        self.type_mapping = None
        self.loaded = False
        
    def load(self) -> bool:
        """Load trained model from checkpoint."""
        from gnn.model import GATModel, LinkPredictor
        
        if not os.path.exists(self.checkpoint_path):
            logger.warning(f"Model checkpoint not found at {self.checkpoint_path}")
            return False
        
        try:
            checkpoint = torch.load(self.checkpoint_path, map_location=self.device)
            
            # Reconstruct model
            self.model = GATModel(
                in_channels=checkpoint["in_channels"],
                hidden_channels=checkpoint["hidden_dim"],
                out_channels=checkpoint["out_channels"],
                heads=8
            ).to(self.device)
            
            self.predictor = LinkPredictor(
                in_channels=checkpoint["out_channels"]
            ).to(self.device)
            
            # Load weights
            self.model.load_state_dict(checkpoint["model_state"])
            self.predictor.load_state_dict(checkpoint["predictor_state"])
            
            # Load mappings
            self.node_mapping = checkpoint.get("node_mapping")
            self.type_mapping = checkpoint.get("type_mapping")
            
            # Set to eval mode
            self.model.eval()
            self.predictor.eval()
            
            self.loaded = True
            logger.info("GNN model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading GNN model: {e}")
            return False
    
    @torch.no_grad()
    def predict_links(
        self,
        drug_ids: List[str],
        disease_ids: List[str],
        graph_engine,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Predict links between drugs and diseases.
        
        Args:
            drug_ids: List of drug node IDs
            disease_ids: List of disease node IDs
            graph_engine: Connected GraphEngine
            top_k: Number of top predictions to return
        
        Returns:
            List of prediction dicts with drug, disease, score
        """
        if not self.loaded:
            logger.error("Model not loaded. Call load() first.")
            return []
        
        if not graph_engine.is_connected():
            logger.error("Graph engine not connected.")
            return []
        
        # Load graph data
        from gnn.data_loader import load_graph_from_neo4j
        data = load_graph_from_neo4j(graph_engine)
        
        if data is None:
            logger.error("No graph data available.")
            return []
        
        # Move to device
        x = data.x.to(self.device)
        edge_index = data.edge_index.to(self.device)
        edge_attr = data.edge_attr.to(self.device) if data.edge_attr is not None else None
        
        # Get node embeddings
        z = self.model(x, edge_index, edge_attr)
        
        # Create reverse mapping (node_id -> idx)
        if hasattr(data, 'node_id_to_idx'):
            id_to_idx = data.node_id_to_idx
        else:
            id_to_idx = {node_id: idx for idx, node_id in enumerate(data.node_ids)}
        
        # Filter to valid IDs
        valid_drugs = [did for did in drug_ids if did in id_to_idx]
        valid_diseases = [did for did in disease_ids if did in id_to_idx]
        
        if not valid_drugs or not valid_diseases:
            logger.warning("No valid drug/disease IDs found in graph.")
            return []
        
        # Predict scores for all drug-disease pairs
        predictions = []
        
        for drug_id in valid_drugs:
            drug_idx = id_to_idx[drug_id]
            drug_emb = z[drug_idx]
            
            for disease_id in valid_diseases:
                disease_idx = id_to_idx[disease_id]
                disease_emb = z[disease_idx]
                
                # Predict link probability
                score = self.predictor(drug_emb.unsqueeze(0), disease_emb.unsqueeze(0)).item()
                
                predictions.append({
                    "drug_id": drug_id,
                    "disease_id": disease_id,
                    "score": score
                })
        
        # Sort by score and return top_k
        predictions.sort(key=lambda x: x["score"], reverse=True)
        return predictions[:top_k]
    
    def get_drug_disease_paths(
        self,
        drug_id: str,
        disease_id: str,
        graph_engine,
        max_path_length: int = 3
    ) -> List[Dict]:
        """
        Find graph paths between a drug and disease.
        Returns paths as evidence for predictions.
        """
        if not graph_engine.is_connected():
            return []
        
        # Note: max_path_length must be literal in pattern, not parameterized
        cypher = f"""
        MATCH path = (d:Entity {{entity_id: $drug_id}})-[*1..{max_path_length}]-(dis:Entity {{entity_id: $disease_id}})
        RETURN 
            [n IN nodes(path) | n.entity_id] AS node_ids,
            [n IN nodes(path) | n.entity_type] AS node_types,
            length(path) AS path_length,
            reduce(conf = 1.0, r IN relationships(path) | conf * COALESCE(r.confidence, 0.5)) AS path_confidence
        ORDER BY path_confidence DESC
        LIMIT 5
        """
        
        try:
            with graph_engine.driver.session(database=graph_engine.database) as session:
                result = session.run(cypher, drug_id=drug_id, disease_id=disease_id)
                paths = []
                for record in result:
                    paths.append({
                        "nodes": record["node_ids"],
                        "types": record["node_types"],
                        "length": record["path_length"],
                        "confidence": record["path_confidence"]
                    })
                return paths
        except Exception as e:
            logger.error(f"Error finding paths: {e}")
            return []


# Global predictor instance
_predictor = None


def get_predictor() -> GNNPredictor:
    """Get or create global predictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = GNNPredictor()
        _predictor.load()
    return _predictor
