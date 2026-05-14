"""
Explanation schema for DRIPE v2 structured output.
"""
from pydantic import BaseModel, Field
from typing import Optional
from schemas.explanation import EvidenceTier


class ExplanationBasis(BaseModel):
    graph_paths_count: int = 0
    literature_chunks: int = 0
    trial_count: int = 0
    evidence_tier: EvidenceTier = EvidenceTier.INSUFFICIENT
    is_known_indication: bool = False


class StructuredExplanation(BaseModel):
    structured_summary: str = Field(..., max_length=500)
    plain_language_summary: str = Field(..., max_length=300)
    uncertainty_statement: str = Field(..., max_length=300)
    basis: ExplanationBasis = Field(default_factory=ExplanationBasis)
