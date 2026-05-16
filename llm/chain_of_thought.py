"""
Chain-of-thought explanation for DRIPE v2.
Produces structured JSON output anchored to supplied evidence.
Uses a fallback chain: primary LLM -> secondary LLM -> rule-based.
"""
import json
import logging
from typing import Optional

from llm.client import (
    get_llm_client,
    PRIMARY_MODEL,
    SECONDARY_MODEL,
    PRIMARY_TIMEOUT,
    SECONDARY_TIMEOUT,
    check_spend,
    increment_spend,
)
from llm.explanation_schema import StructuredExplanation, ExplanationBasis
from schemas.explanation import EvidenceTier, NoveltyBucket

logger = logging.getLogger(__name__)

PROMPT_PATH = "llm/prompts/explanation_json_prompt.txt"


def _load_prompt_template() -> str:
    with open(PROMPT_PATH) as f:
        return f.read()


def _determine_tier(path_count: int, lit_count: int, trial_count: int) -> EvidenceTier:
    total = path_count + lit_count + trial_count
    if total >= 10:
        return EvidenceTier.STRONG
    elif total >= 5:
        return EvidenceTier.MODERATE
    elif total >= 1:
        return EvidenceTier.WEAK
    return EvidenceTier.INSUFFICIENT


def _build_rule_based_explanation(
    drug: str,
    disease: str,
    paths: list,
    literature: list,
    trials: list,
    counter_evidence: list,
    novelty_bucket: Optional[NoveltyBucket] = None,
) -> StructuredExplanation:
    """Assemble a deterministic explanation from pipeline artifacts."""
    path_count = len(paths)
    lit_count = len(literature)
    trial_count = len(trials)
    total_evidence = path_count + lit_count + trial_count

    path_types = set()
    for p in paths:
        if isinstance(p, dict):
            path_types.add(p.get("path_type", ""))
        elif isinstance(p, str):
            path_types.add(p)
    path_types_str = ", ".join(sorted(path_types)) if path_types else "unknown"

    trial_clause = ""
    if trial_count > 0:
        trial_clause = f" {trial_count} clinical trial(s) found."

    sparsity_flag = ""
    if total_evidence < 5:
        sparsity_flag = " Evidence is sparse and should be interpreted with caution."

    if path_count == 1:
        path_label = "a single graph path"
    else:
        path_label = f"{path_count} graph paths"

    structured_summary = (
        f"{drug} is connected to {disease} through {path_label} "
        f"({path_types_str}).{trial_clause} "
        f"Literature support: {lit_count} chunk(s).{sparsity_flag}"
    )

    trial_plain = ""
    if trial_count > 0:
        trial_plain = f" It has been investigated in {trial_count} clinical trial(s)."

    plain_language_summary = (
        f"{drug} has known or predicted connections to {disease}.{trial_plain}{sparsity_flag}"
    )

    tier = _determine_tier(path_count, lit_count, trial_count)
    uncertainty_map = {
        EvidenceTier.STRONG: (
            "Multiple independent evidence sources converge on this relationship."
        ),
        EvidenceTier.MODERATE: (
            "Evidence exists but is not yet convergent across multiple source types."
        ),
        EvidenceTier.WEAK: (
            "Limited evidence available. This is an early-stage hypothesis."
        ),
        EvidenceTier.INSUFFICIENT: (
            "Insufficient evidence to assess this relationship. Further research is needed."
        ),
    }

    counter_text = ""
    if counter_evidence:
        ce_types = set()
        for c in counter_evidence:
            if isinstance(c, dict):
                ce_types.add(c.get("type", str(c)))
            elif hasattr(c, "type"):
                ce_types.add(c.type)
            else:
                ce_types.add(str(c))
        if "sparse_support" in ce_types:
            counter_text = " Support from retrieved literature is minimal."

    uncertainty_statement = uncertainty_map.get(tier, uncertainty_map[EvidenceTier.INSUFFICIENT]) + counter_text

    return StructuredExplanation(
        structured_summary=structured_summary[:500],
        plain_language_summary=plain_language_summary[:300],
        uncertainty_statement=uncertainty_statement[:300],
        basis=ExplanationBasis(
            graph_paths_count=path_count,
            literature_chunks=lit_count,
            trial_count=trial_count,
            evidence_tier=tier,
            is_known_indication=(
                novelty_bucket == NoveltyBucket.KNOWN_INDICATION
                if novelty_bucket
                else False
            ),
        ),
    )


def _parse_llm_response(response: str) -> Optional[dict]:
    """Try to parse LLM response as JSON. Returns None on failure."""
    if not response:
        return None
    try:
        data = json.loads(response)
        if not isinstance(data, dict):
            return None
        return data
    except json.JSONDecodeError:
        return None


def _extract_explanation(data: dict) -> Optional[StructuredExplanation]:
    """Build StructuredExplanation from parsed JSON if minimum fields present."""
    structured = data.get("structured_summary")
    plain = data.get("plain_language_summary")
    if not structured or not plain:
        return None
    return StructuredExplanation(
        structured_summary=str(structured)[:500],
        plain_language_summary=str(plain)[:300],
        uncertainty_statement=str(data.get("uncertainty_statement", ""))[:300],
        basis=ExplanationBasis(),
    )


async def generate_cot_explanation(
    drug: str,
    disease: str,
    paths: list,
    literature: list = None,
    safety: dict = None,
    trials: list = None,
    counter_evidence: list = None,
    novelty_bucket: Optional[NoveltyBucket] = None,
) -> tuple:
    """Generate structured explanation. Returns (StructuredExplanation, path, was_retried).

    The `path` return value is one of: 'primary', 'secondary', 'rule_based'.
    The `was_retried` is True if any LLM retry occurred.
    """
    if literature is None:
        literature = []
    if safety is None:
        safety = {}
    if trials is None:
        trials = []
    if counter_evidence is None:
        counter_evidence = []

    template = _load_prompt_template()
    prompt = template.format(
        drug_name=drug,
        disease_name=disease,
        paths=json.dumps(paths[:3], indent=2),
        literature=json.dumps(literature[:3], indent=2),
        trials=json.dumps(trials[:3], indent=2),
        counter=json.dumps(counter_evidence[:3], indent=2),
    )

    client = get_llm_client()
    overall_retried = False

    # Attempt 1: Primary model (openrouter/free)
    text, ok = await client.generate(
        prompt,
        model=PRIMARY_MODEL,
        timeout=PRIMARY_TIMEOUT,
    )
    if ok:
        parsed = _parse_llm_response(text)
        if parsed:
            built = _extract_explanation(parsed)
            if built:
                built.basis = ExplanationBasis(
                    graph_paths_count=len(paths),
                    literature_chunks=len(literature),
                    trial_count=len(trials),
                    evidence_tier=_determine_tier(len(paths), len(literature), len(trials)),
                    is_known_indication=False,
                )
                return built, "primary", False
        logger.warning(f"Primary model returned unparseable output for {drug}")

    overall_retried = True
    logger.info(f"Primary LLM failed for {drug}, checking secondary fallback")

    # Attempt 2: Secondary model (openrouter/auto) with spend cap
    if check_spend():
        text2, ok2 = await client.generate(
            prompt,
            model=SECONDARY_MODEL,
            timeout=SECONDARY_TIMEOUT,
        )
        if ok2:
            parsed2 = _parse_llm_response(text2)
            if parsed2:
                built2 = _extract_explanation(parsed2)
                if built2:
                    increment_spend()
                    built2.basis = ExplanationBasis(
                        graph_paths_count=len(paths),
                        literature_chunks=len(literature),
                        trial_count=len(trials),
                        evidence_tier=_determine_tier(len(paths), len(literature), len(trials)),
                        is_known_indication=False,
                    )
                    logger.info(f"Secondary fallback succeeded for {drug}")
                    return built2, "secondary", True
        logger.warning(f"Secondary LLM also failed for {drug}")
    else:
        logger.info(f"Secondary fallback skipped for {drug} (spend cap reached or disabled)")

    # Final: Rule-based fallback
    logger.info(f"Using rule-based fallback for {drug}")
    fallback = _build_rule_based_explanation(
        drug=drug,
        disease=disease,
        paths=paths,
        literature=literature,
        trials=trials,
        counter_evidence=counter_evidence,
        novelty_bucket=novelty_bucket,
    )
    return fallback, "rule_based", overall_retried
