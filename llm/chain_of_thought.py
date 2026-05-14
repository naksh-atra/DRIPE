"""
Chain-of-thought explanation for DRIPE v2.
Produces structured JSON output anchored to supplied evidence.
"""
import json
import logging
from llm.client import get_llm_client
from llm.explanation_schema import StructuredExplanation, ExplanationBasis
from schemas.explanation import EvidenceTier

logger = logging.getLogger(__name__)

PROMPT_PATH = "llm/prompts/explanation_json_prompt.txt"


def _load_prompt_template() -> str:
    with open(PROMPT_PATH) as f:
        return f.read()


async def generate_cot_explanation(
    drug: str,
    disease: str,
    paths: list,
    literature: list = None,
    safety: dict = None,
    trials: list = None,
    counter_evidence: list = None,
) -> StructuredExplanation:
    """Generate structured explanation from supplied evidence."""
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
    response = await client.generate(prompt)

    try:
        data = json.loads(response)
        return StructuredExplanation(
            structured_summary=data.get("structured_summary", ""),
            plain_language_summary=data.get("plain_language_summary", ""),
            uncertainty_statement=data.get("uncertainty_statement", ""),
            basis=ExplanationBasis(
                graph_paths_count=len(paths),
                literature_chunks=len(literature),
                trial_count=len(trials),
                evidence_tier=_determine_tier(len(paths), len(literature), len(trials)),
                is_known_indication=False,
            ),
        )
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to parse LLM response as JSON: {e}")
        return StructuredExplanation(
            structured_summary="Explanation generation failed.",
            plain_language_summary="Could not generate summary.",
            uncertainty_statement="LLM output could not be parsed.",
        )


def _determine_tier(path_count: int, lit_count: int, trial_count: int) -> EvidenceTier:
    total = path_count + lit_count + trial_count
    if total >= 10:
        return EvidenceTier.STRONG
    elif total >= 5:
        return EvidenceTier.MODERATE
    elif total >= 1:
        return EvidenceTier.WEAK
    return EvidenceTier.INSUFFICIENT
