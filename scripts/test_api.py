"""Test the DRIPE API endpoint."""
import requests
import json

try:
    r = requests.post(
        "http://localhost:8000/query",
        json={"disease": "C0006826"},
        timeout=90
    )
    
    data = r.json()
    
    print(f"Status: {r.status_code}")
    print(f"Disease: {data.get('query_disease')}")
    print(f"Candidates: {len(data.get('candidates', []))}")
    
    for cand in data.get('candidates', []):
        print(f"\n--- Candidate {cand['rank']} ---")
        print(f"Drug: {cand['drug_id']}")
        print(f"Tier: {cand['confidence_tier']}")
        print(f"GNN Score: {cand['gnn_similarity_score']:.4f}")
        print(f"Literature: {cand['literature_support_count']} chunks")
        
        if cand.get('llm_explanation'):
            print(f"LLM: {cand['llm_explanation'][:100]}...")
        else:
            print("LLM: No explanation")
            
except Exception as e:
    print(f"Error: {e}")
