import torch
from transformers import AutoTokenizer, AutoModel
import logging

logger = logging.getLogger(__name__)

class MedGemmaEmbedder:
    def __init__(self, model_id="google/medgemma-2b"): # Placeholder for real 4B/9B model
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = AutoModel.from_pretrained(
            model_id, 
            torch_dtype=torch.bfloat16 if self.device == "cuda" else torch.float32
        ).to(self.device)
        
        if self.device == "cpu":
            logger.warning("RAG Layer running on CPU. Inference will be slow.")

    def embed_text(self, text: str) -> torch.Tensor:
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use mean pooling or CLS token
            embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings.cpu()
