import json
import os
import sys

def run_regression_test():
    latest_benchmark_path = "evaluation/latest_benchmark.json"
    
    if not os.path.exists(latest_benchmark_path):
        print("No previous benchmark found. Skipping regression check.")
        return 0

    with open(latest_benchmark_path, 'r') as f:
        data = json.load(f)
        recall_10 = data.get("recall_10", 0.0)

    # Hard threshold from Phase 1 specs: 
    # Fail if Recall@10 drops by more than 5 percentage points (0.05)
    # For now, we compare against a fixed target for the skeleton
    TARGET_RECALL = 0.65
    
    if recall_10 < TARGET_RECALL - 0.05:
        print(f"REGRESSION DETECTED: Recall@10 ({recall_10}) is below threshold ({TARGET_RECALL - 0.05})")
        return 1
    
    print(f"Benchmark PASSED: Recall@10 = {recall_10}")
    return 0

if __name__ == "__main__":
    sys.exit(run_regression_test())
