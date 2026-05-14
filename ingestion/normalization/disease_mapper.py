"""
Disease ID normalization for DRIPE ingestion.
Maps various disease identifiers to canonical UMLS CUIs.
"""
import yaml
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "disease_program.yaml"


def _load_cfg() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def resolve_disease_to_cui(disease_name: str) -> Optional[str]:
    """Resolve a disease name/alias to its canonical CUI."""
    cfg = _load_cfg()
    primary = cfg["primary_disease"]
    normalized = disease_name.strip().lower()

    if normalized in [a.lower() for a in primary["allowed_aliases"]]:
        return primary["canonical_cui"]

    for adj in cfg.get("adjacency_diseases", []):
        if normalized == adj["name"].lower():
            return adj["canonical_cui"]

    return None
