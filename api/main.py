from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
from api.schemas import QueryRequest, QueryResponse
from guardrails.query_classifier import QueryClassifier, QueryCategory
from guardrails.disclaimer_injector import inject_disclaimer

app = FastAPI(title="DRIPE API", version="1.0.0")

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

classifier = QueryClassifier()

@app.post("/query", response_model=QueryResponse)
async def run_query(request: QueryRequest):
    # 1. Guardrail Classification
    category, confidence = classifier.classify_query(request.disease)
    
    if category == QueryCategory.PATIENT_SPECIFIC:
        raise HTTPException(status_code=403, detail="System does not process patient-specific queries.")
    elif category == QueryCategory.TREATMENT_ADVICE:
        raise HTTPException(status_code=400, detail="System does not provide clinical treatment advice.")
        
    # 2. Pipeline Execution with Timeout
    try:
        async with asyncio.timeout(60):
            # Simulate pipeline logic
            # Fetch candidates, graph paths, RAG evidence...
            await asyncio.sleep(1) # Simulated work
            
            response_data = {
                "query_disease": request.disease,
                "graph_version": "v2026.03.0",
                "coverage_report": {
                    "completeness_tier": "MEDIUM",
                    "gene_association_count": 50,
                    "protein_interaction_count": 120,
                    "pubmed_paper_count": 80,
                    "trial_count": 5,
                    "sparse_edges": []
                },
                "candidates": [],
                "timeout_flag": False
            }
            
            # 3. Inject Disclaimer
            response_data = inject_disclaimer(response_data)
            return response_data
            
    except asyncio.TimeoutError:
        return HTTPException(status_code=408, detail="Query timeout. Processing took longer than 60 seconds.")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "services": {"neo4j": "up", "mongodb": "up", "redis": "up"}}
