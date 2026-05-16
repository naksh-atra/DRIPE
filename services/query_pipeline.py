"""
Query pipeline for DRIPE v2.
Orchestrates the full query flow: resolve -> graph -> rank -> retrieve -> explain -> respond.
"""
import asyncio
import logging
import time
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
from llm.chain_of_thought import generate_cot_explanation, _build_rule_based_explanation
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
    query_result = resolve_disease(request.disease_input)
    if query_result.query_status != QueryStatus.ACCEPTED:
        return QueryResponse(
            query=query_result.model_dump(),
            candidates=[],
        )

    disease_cui = query_result.canonical_disease_id

    coverage = await coverage_reporter.get_coverage(disease_cui)
    coverage_report = CoverageReport(
        graph_density_note=f"Graph contains graph data for {disease_cui}",
        literature_density_note="FAISS index available for semantic search",
        trial_evidence_note="ClinicalTrials data available",
        known_limitations=coverage.get("sparse_edges", []),
    )

    paths = await path_traversal.get_drug_disease_paths(disease_cui)

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

    trial_counts = {}
    if graph_engine.is_connected():
        drug_ids_for_trials = list(set(p["drug_id"] for p in paths))
        for d_id in drug_ids_for_trials:
            r = graph_engine.run_cypher(
                "MATCH (n:Entity {entity_id: $eid})-[rb:BIOREL {type: 'TRIAL_INVESTIGATES'}]->() RETURN count(rb) AS c",
                {"eid": d_id}
            )
            trial_counts[d_id] = r[0]["c"] if r else 0

    candidates = []
    for i, path in enumerate(paths):
        drug_id = path["drug_id"]
        gnn_score = gnn_scores.get(drug_id, 0.0)

        graph_score = path.get("path_confidence", 0.5)
        trial_count = trial_counts.get(drug_id, 0)
        trial_score = min(trial_count / 10.0, 1.0)

        literature = []
        if rag_retriever:
            raw_results = rag_retriever.retrieve_for_candidate(
                drug_name=drug_id,
                disease_name=disease_cui,
                top_k=3,
            )
            literature = raw_results

        evidence_score = min(len(literature) / 5.0, 1.0) if literature else 0.0

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

    candidates.sort(key=lambda c: c.ranking_scores.composite_score, reverse=True)

    # LLM explanations for top 3 (parallel, with cumulative budget)
    top = candidates[:3]
    if top:
        llm_start = time.monotonic()

        async def explain_one(cand: Candidate):
            if time.monotonic() - llm_start > 60:
                logger.info(f"Skipping LLM for {cand.drug_name}: budget exceeded")
                rule = _build_rule_based_explanation(
                    drug=cand.drug_name,
                    disease=disease_cui,
                    paths=[p.path_type for p in cand.supporting_paths],
                    literature=[
                        {"text": e.snippet, "pmid": e.identifier}
                        for e in (cand.retrieved_evidence or [])
                    ],
                    trials=[],
                    counter_evidence=cand.counter_evidence,
                    novelty_bucket=cand.novelty_bucket,
                )
                cand.explanation = rule
                return cand.drug_name, "rule_based", False

            lit_for_prompt = [
                {"text": e.snippet, "pmid": e.identifier}
                for e in (cand.retrieved_evidence or [])
            ]
            exp, path, retried = await generate_cot_explanation(
                drug=cand.drug_name,
                disease=disease_cui,
                paths=[p.path_type for p in cand.supporting_paths],
                literature=lit_for_prompt,
                novelty_bucket=cand.novelty_bucket,
            )
            cand.explanation = exp
            return cand.drug_name, path, retried

        try:
            llm_results = await asyncio.wait_for(
                asyncio.gather(*[explain_one(c) for c in top], return_exceptions=True),
                timeout=65,
            )
            rule_based_count = 0
            for result in llm_results:
                if isinstance(result, Exception):
                    logger.warning(f"LLM task exception: {result}")
                    rule_based_count += 1
                    continue
                name, path, retried = result
                logger.info(f"Explanation for {name}: path={path}, retried={retried}")
                if path == "rule_based":
                    rule_based_count += 1

            if rule_based_count >= 2:
                logger.warning(f"High fallback rate: {rule_based_count}/3 candidates used rule-based explanations")

        except asyncio.TimeoutError:
            logger.warning("LLM explanation budget exceeded (65s timeout)")
            for cand in top:
                if cand.explanation is None:
                    rule = _build_rule_based_explanation(
                        drug=cand.drug_name,
                        disease=disease_cui,
                        paths=[p.path_type for p in cand.supporting_paths],
                        literature=[
                            {"text": e.snippet, "pmid": e.identifier}
                            for e in (cand.retrieved_evidence or [])
                        ],
                        trials=[],
                        counter_evidence=cand.counter_evidence,
                        novelty_bucket=cand.novelty_bucket,
                    )
                    cand.explanation = rule

    # Ranks 4+ get rule-based explanations
    for cand in candidates[3:]:
        if cand.explanation is None:
            rule = _build_rule_based_explanation(
                drug=cand.drug_name,
                disease=disease_cui,
                paths=[p.path_type for p in cand.supporting_paths],
                literature=[
                    {"text": e.snippet, "pmid": e.identifier}
                    for e in (cand.retrieved_evidence or [])
                ],
                trials=[],
                counter_evidence=cand.counter_evidence,
                novelty_bucket=cand.novelty_bucket,
            )
            cand.explanation = rule

    return QueryResponse(
        query=query_result.model_dump(),
        program_scope=ProgramScope(
            primary_disease="rheumatoid arthritis",
            adjacent_diseases_considered=query_result.adjacency_diseases,
        ),
        coverage_report=coverage_report,
        candidates=candidates,
    )
