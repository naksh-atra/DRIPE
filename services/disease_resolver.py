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
    primary_name = cfg["primary_disease"]["name"]
    aliases = cfg["primary_disease"]["allowed_aliases"]
    return [primary_name] + aliases


def get_supported_diseases_for_error() -> List[str]:
    cfg = load_config()
    primary = cfg["primary_disease"]
    adj = [d["name"] for d in cfg.get("adjacency_diseases", [])]
    return [primary["name"]] + adj


def resolve_disease(disease_input: str) -> QueryResult:
    cfg = load_config()
    primary = cfg["primary_disease"]
    rejected = cfg.get("rejected_aliases", [])
    adj_diseases = [d["name"] for d in cfg.get("adjacency_diseases", [])]

    normalized = disease_input.strip().lower()

    # Check rejected aliases first
    if normalized in [a.lower() for a in rejected]:
        return QueryResult(
            disease_input=disease_input,
            query_status=QueryStatus.REJECTED_UNSUPPORTED_DISEASE,
            rejection_reason=f"'{disease_input}' is ambiguous. Supported diseases: {', '.join(get_supported_diseases_for_error())}."
        )

    # Check primary disease aliases
    if normalized in [a.lower() for a in primary["allowed_aliases"]]:
        return QueryResult(
            disease_input=disease_input,
            canonical_disease_id=primary["canonical_cui"],
            query_status=QueryStatus.ACCEPTED,
            adjacency_diseases=[d["canonical_cui"] for d in cfg.get("adjacency_diseases", [])]
        )

    # Unsupported disease
    return QueryResult(
        disease_input=disease_input,
        query_status=QueryStatus.REJECTED_UNSUPPORTED_DISEASE,
        rejection_reason=f"Unsupported disease. Supported diseases: {', '.join(get_supported_diseases_for_error())}."
    )
