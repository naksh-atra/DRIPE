from enum import Enum
from typing import Tuple

class QueryCategory(Enum):
    PATIENT_SPECIFIC = "PATIENT_SPECIFIC"
    TREATMENT_ADVICE = "TREATMENT_ADVICE"
    RESEARCH_QUERY = "RESEARCH_QUERY"

class QueryClassifier:
    def __init__(self, model_path: str = None):
        self.threshold = 0.80
        # In full implementation, load distilbert-base-uncased
        self.model = None 

    def classify_query(self, query: str) -> Tuple[QueryCategory, float]:
        """
        Classifies incoming queries based on intent.
        Returns (Category, Confidence).
        """
        query_lower = query.lower()
        
        # Simple heuristic-based simulation for the skeleton
        if any(word in query_lower for word in ["prescribe", "should i take", "treatment for me"]):
            return QueryCategory.TREATMENT_ADVICE, 0.95
        if any(word in query_lower for word in ["my age", "my symptoms", "i have"]):
            return QueryCategory.PATIENT_SPECIFIC, 0.90
            
        return QueryCategory.RESEARCH_QUERY, 0.85
