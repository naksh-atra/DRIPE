"""
DRIPE v2 API — FastAPI endpoint with v2 response contract.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from schemas.query import QueryRequest, QueryStatus
from schemas.response import QueryResponse
from guardrails.query_classifier import QueryClassifier, QueryCategory
from guardrails.disclaimer_injector import DISCLAIMER_TEXT
from graph.graph_builder import GraphEngine
from graph.coverage_report import CoverageReporter
from graph.path_traversal import PathTraversal
from gnn.inference import get_predictor
from rag.retriever import get_retriever
from services.query_pipeline import run_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DRIPE v2 API", version="2.0.0")

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
graph_engine = GraphEngine()
graph_engine.connect()

classifier = QueryClassifier()
coverage_reporter = CoverageReporter(graph_engine)
path_traversal = PathTraversal(graph_engine)
gnn_predictor = get_predictor()
rag_retriever = get_retriever()


@app.post("/query", response_model=QueryResponse)
async def run_query(request: QueryRequest):
    # Guardrail classification
    category, confidence = classifier.classify_query(request.disease_input)

    if category == QueryCategory.PATIENT_SPECIFIC:
        raise HTTPException(status_code=403, detail="System does not process patient-specific queries.")
    elif category == QueryCategory.TREATMENT_ADVICE:
        raise HTTPException(status_code=400, detail="System does not provide clinical treatment advice.")

    # Run pipeline
    try:
        response = await asyncio.wait_for(
            run_pipeline(
                request=request,
                graph_engine=graph_engine,
                path_traversal=path_traversal,
                coverage_reporter=coverage_reporter,
                gnn_predictor=gnn_predictor,
                rag_retriever=rag_retriever,
            ),
            timeout=120,
        )
        response.research_only_disclaimer = DISCLAIMER_TEXT
        return response
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Query timeout.")
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    neo4j_status = "up" if graph_engine.is_connected() else "down"
    return {
        "status": "healthy" if neo4j_status == "up" else "degraded",
        "version": "2.0.0",
        "services": {"neo4j": neo4j_status, "rag": "up", "gnn": "loaded" if gnn_predictor.loaded else "unavailable"},
    }
