"""
Disease resolver for DRIPE v2.
Resolves disease input strings to canonical IDs using the disease program config.
"""
import yaml
import logging
from pathlib import Path
from typing import Optional, Tuple, List

from schemas.query import QueryStatus, QueryResult

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent / "config" / "disease_program.yaml"

_resolved_config = None


def load_config() -> dict:
    global _resolved_config
    if _resolved_config is not None:
        return _resolved_config
    with open(CONFIG_PATH) as f:
        _resolved_config = yaml.safe_load(f)
    return _resolved_config


def get_supported_diseases() -> List[str]:
    cfg = load_config()
    supported = list(cfg["primary_disease"]["allowed_aliases"])
    for adj in cfg.get("adjacency_diseases", []):
        if not adj.get("graph_context_only", True):
            supported.extend(adj.get("allowed_aliases", [adj["name"]]))
    return supported


def get_supported_diseases_for_error() -> List[str]:
    cfg = load_config()
    names = [cfg["primary_disease"]["name"]]
    for adj in cfg.get("adjacency_diseases", []):
        if not adj.get("graph_context_only", True):
            names.append(adj["name"])
    return names


def resolve_disease(disease_input: str) -> QueryResult:
    cfg = load_config()
    primary = cfg["primary_disease"]
    rejected = cfg.get("rejected_aliases", [])
    adj_diseases = cfg.get("adjacency_diseases", [])

    normalized = disease_input.strip().lower()

    if normalized in [a.lower() for a in rejected]:
        return QueryResult(
            disease_input=disease_input,
            query_status=QueryStatus.REJECTED_UNSUPPORTED_DISEASE,
            rejection_reason=f"'{disease_input}' is ambiguous. Supported: {', '.join(get_supported_diseases_for_error())}."
        )

    if normalized in [a.lower() for a in primary["allowed_aliases"]]:
        return QueryResult(
            disease_input=disease_input,
            canonical_disease_id=primary["canonical_cui"],
            query_status=QueryStatus.ACCEPTED,
            adjacency_diseases=[d["canonical_cui"] for d in adj_diseases]
        )

    for adj in adj_diseases:
        if adj.get("graph_context_only", True):
            continue
        if normalized in [a.lower() for a in adj.get("allowed_aliases", [adj["name"]])]:
            return QueryResult(
                disease_input=disease_input,
                canonical_disease_id=adj["canonical_cui"],
                query_status=QueryStatus.ACCEPTED,
                adjacency_diseases=[d["canonical_cui"] for d in adj_diseases if d["canonical_cui"] != adj["canonical_cui"]]
            )

    return QueryResult(
        disease_input=disease_input,
        query_status=QueryStatus.REJECTED_UNSUPPORTED_DISEASE,
        rejection_reason=f"Unsupported disease. Supported: {', '.join(get_supported_diseases_for_error())}."
    )
