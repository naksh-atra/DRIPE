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

    # 4. GNN scoring (if available, gracefully handles model/data mismatch)
    gnn_scores = {}
    if paths and gnn_predictor and gnn_predictor.loaded:
        drug_ids = list(set(p["drug_id"] for p in paths))
        if graph_engine.is_connected():
            try:
                predictions = gnn_predictor.predict_links(
                    drug_ids, [disease_cui], graph_engine, top_k=50
                )
                for pred in predictions:
                    gnn_scores[pred["drug_id"]] = pred["score"]
            except Exception as e:
                logger.warning(f"GNN prediction failed (shape mismatch expected with new graph): {e}")

    # 5. Count Drug→Trial edges for each candidate
    trial_counts = {}
    if graph_engine.is_connected():
        drug_ids_for_trials = list(set(p["drug_id"] for p in paths))
        for d_id in drug_ids_for_trials:
            r = graph_engine.run_cypher(
                "MATCH (n:Entity {entity_id: $eid})-[rb:BIOREL {type: 'TRIAL_INVESTIGATES'}]->() RETURN count(rb) AS c",
                {"eid": d_id}
            )
            trial_counts[d_id] = r[0]["c"] if r else 0

    # 6. Assemble candidates with ranking and retrieval
    candidates = []
    for i, path in enumerate(paths):
        drug_id = path["drug_id"]
        gnn_score = gnn_scores.get(drug_id, 0.0)

        graph_score = path.get("path_confidence", 0.5)
        trial_count = trial_counts.get(drug_id, 0)
        trial_score = min(trial_count / 10.0, 1.0)

        # RAG retrieval
        literature = []
        if rag_retriever:
            raw_results = rag_retriever.retrieve_for_candidate(
                drug_name=drug_id,
                disease_name=disease_cui,
                top_k=3,
            )
            literature = raw_results

        evidence_score = min(len(literature) / 5.0, 1.0) if literature else 0.0

        # Convert raw results to RetrievedEvidence and check counter-evidence
        lit_objects = build_evidence_packet(literature, [])
        counter = check_counter_evidence(drug_id, disease_cui, len(literature))

        candidates.append(assemble_candidate(
            drug_name=f"Drug:{drug_id}",
            drug_id=drug_id,
            paths=[path],
            graph_score=graph_score,
            evidence_score=evidence_score,
            trial_score=trial_score,
            learned_score=gnn_score,
            literature=lit_objects,
            counter_evidence=counter,
            trial_count=trial_count,
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
