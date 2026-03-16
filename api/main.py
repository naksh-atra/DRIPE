from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
from datetime import datetime
from api.schemas import QueryRequest, QueryResponse, CoverageReport
from guardrails.query_classifier import QueryClassifier, QueryCategory
from guardrails.disclaimer_injector import DISCLAIMER_TEXT

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
        response_data = await asyncio.wait_for(simulate_pipeline(request.disease), timeout=60)
        return response_data
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Query timeout.")

async def simulate_pipeline(disease: str) -> QueryResponse:
    """Mock pipeline — returns a valid Pydantic QueryResponse for skeleton testing."""
    await asyncio.sleep(1)
    return QueryResponse(
        query_disease=disease,
        query_timestamp=datetime.utcnow(),
        graph_version="v2026.03.0",
        coverage_report=CoverageReport(
            completeness_tier="MEDIUM",
            gene_association_count=50,
            protein_interaction_count=120,
            pubmed_paper_count=80,
            trial_count=5,
            sparse_edges=[]
        ),
        candidates=[],
        disclaimer=DISCLAIMER_TEXT,
        timeout_flag=False
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "services": {"neo4j": "up", "mongodb": "up", "redis": "up"}}
