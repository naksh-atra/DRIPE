"""
Error taxonomy for DRIPE v2 evaluation.
Categories and definitions for failure analysis.
"""
from enum import Enum


class ErrorCategory(str, Enum):
    ONTOLOGY_MISMATCH = "ontology_mismatch"
    GRAPH_SPARSITY = "graph_sparsity"
    HUB_NODE_BIAS = "hub_node_bias"
    UNSUPPORTED_EXPLANATION = "unsupported_explanation"
    LITERATURE_MISMATCH = "literature_retrieval_mismatch"
    TRIAL_MISMATCH = "trial_evidence_mismatch"
    KNOWN_AS_NOVEL = "known_indication_presented_as_novel"
    GENERIC_EXPLANATION = "overly_generic_explanation"
    MISSING_COUNTER_EVIDENCE = "missing_counter_evidence"


ERROR_DESCRIPTIONS = {
    ErrorCategory.ONTOLOGY_MISMATCH: "Disease query doesn't match canonical ID.",
    ErrorCategory.GRAPH_SPARSITY: "Too few paths to rank meaningfully.",
    ErrorCategory.HUB_NODE_BIAS: "Well-studied proteins dominate all paths.",
    ErrorCategory.UNSUPPORTED_EXPLANATION: "LLM adds content not in supplied evidence.",
    ErrorCategory.LITERATURE_MISMATCH: "Retrieved chunk is semantically irrelevant.",
    ErrorCategory.TRIAL_MISMATCH: "Trial endpoint or condition doesn't match use case.",
    ErrorCategory.KNOWN_AS_NOVEL: "Known drug presented as exploratory.",
    ErrorCategory.GENERIC_EXPLANATION: "Explanation is generic ('targets inflammation').",
    ErrorCategory.MISSING_COUNTER_EVIDENCE: "Known negative signal not surfaced.",
}
