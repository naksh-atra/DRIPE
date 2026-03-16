import json
import os

class BenchmarkRunner:
    def __init__(self, gold_standard_path: str = "evaluation/gold_standard.json"):
        self.gold_standard_path = gold_standard_path
        self.metrics = {}

    def run_full_evaluation(self, pipeline_func):
        """
        Runs the full pipeline over the gold standard test set.
        Hides known repurposing relationship during each test.
        """
        if not os.path.exists(self.gold_standard_path):
            return {"error": "Gold standard file missing"}
            
        with open(self.gold_standard_path, 'r') as f:
            test_cases = json.load(f)
            
        results = []
        for case in test_cases:
            # Execute pipeline
            # Calculate recalls and MRR
            pass
            
        return self.metrics

def check_regression(current_mrr: float, previous_mrr: float):
    """Fails CI if performance drops by > 5%."""
    if current_mrr < previous_mrr - 0.05:
        raise Exception(f"Regression detected: {current_mrr} < {previous_mrr - 0.05}")
