"""
Query pipeline for DRIPE v2.
Orchestrates the full query flow: resolve → graph → rank → retrieve → explain → respond.
"""
import asyncio
import logging
from typing import Optional

from schemas.query import QueryRequest, QueryResult, QueryStatus
from schemas.response import QueryResponse, ProgramScope, CoverageReport, Candidate
from services.disease_resolver import resolve_disease
from services.candidate_assembler import assemble_candidate
from graph.graph_builder import GraphEngine
from graph.path_traversal import PathTraversal
from graph.coverage_report import CoverageReporter
from gnn.inference import get_predictor
from rag.retriever import get_retriever
from rag.evidence_packet import build_evidence_packet, check_counter_evidence
from llm.chain_of_thought import generate_cot_explanation
from schemas.explanation import EvidenceTier

logger = logging.getLogger(__name__)


async def run_pipeline(
    request: QueryRequest,
    graph_engine: GraphEngine,
    path_traversal: PathTraversal,
    coverage_reporter: CoverageReporter,
    gnn_predictor=None,
    rag_retriever=None,
) -> QueryResponse:
    """Run the full DRIPE v2 query pipeline."""
    # 1. Resolve disease
    query_result = resolve_disease(request.disease_input)
    if query_result.query_status != QueryStatus.ACCEPTED:
        return QueryResponse(
            query=query_result.model_dump(),
            candidates=[],
        )

    disease_cui = query_result.canonical_disease_id

    # 2. Coverage report
    coverage = await coverage_reporter.get_coverage(disease_cui)
    coverage_report = CoverageReport(
        graph_density_note=f"Graph contains graph data for {disease_cui}",
        literature_density_note="FAISS index available for semantic search",
        trial_evidence_note="ClinicalTrials data available",
        known_limitations=coverage.get("sparse_edges", []),
    )

    # 3. Graph traversal
    paths = await path_traversal.get_drug_disease_paths(disease_cui)

    # 4. GNN scoring (if available)
    gnn_scores = {}
    if paths and gnn_predictor and gnn_predictor.loaded:
        drug_ids = list(set(p["drug_id"] for p in paths))
        if graph_engine.is_connected():
            predictions = gnn_predictor.predict_links(
                drug_ids, [disease_cui], graph_engine, top_k=50
            )
            for pred in predictions:
                gnn_scores[pred["drug_id"]] = pred["score"]

    # 5. Assemble candidates with ranking and retrieval
    candidates = []
    for i, path in enumerate(paths):
        drug_id = path["drug_id"]
        gnn_score = gnn_scores.get(drug_id, 0.0)

        # Graph score from path confidence
        graph_score = path.get("path_confidence", 0.5)

        # RAG retrieval
        literature = []
        if rag_retriever:
            results = rag_retriever.retrieve_for_candidate(
                drug_name=drug_id,
                disease_name=disease_cui,
                top_k=3,
            )
            literature = results

        evidence_score = min(len(literature) / 5.0, 1.0) if literature else 0.0

        candidates.append(assemble_candidate(
            drug_name=f"Drug:{drug_id}",
            drug_id=drug_id,
            paths=[path],
            graph_score=graph_score,
            evidence_score=evidence_score,
            trial_score=0.0,
            learned_score=gnn_score,
            literature=[],  # Will be converted properly
            trial_count=0,
        ))

    # Sort by composite score
    candidates.sort(key=lambda c: c.ranking_scores.composite_score, reverse=True)

    # 6. LLM explanations for top 5
    for cand in candidates[:5]:
        try:
            lit_for_prompt = [
                {"text": e.snippet, "pmid": e.identifier}
                for e in (cand.retrieved_evidence or [])
            ]
            explanation = await generate_cot_explanation(
                drug=cand.drug_name,
                disease=disease_cui,
                paths=[p.path_type for p in cand.supporting_paths],
                literature=lit_for_prompt,
            )
            cand.explanation = explanation
        except Exception as e:
            logger.error(f"LLM error for {cand.drug_name}: {e}")

    return QueryResponse(
        query=query_result.model_dump(),
        program_scope=ProgramScope(
            primary_disease="rheumatoid arthritis",
            adjacent_diseases_considered=query_result.adjacency_diseases,
        ),
        coverage_report=coverage_report,
        candidates=candidates,
    )
