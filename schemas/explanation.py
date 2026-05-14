"""
Explanation and scoring schemas for DRIPE v2.
"""
from enum import Enum
from pydantic import BaseModel
from typing import List, Optional


class NoveltyBucket(str, Enum):
    KNOWN_INDICATION = "known_indication"
    ADJACENT_OFFLABEL = "adjacent_offlabel"
    TRIAL_EXPLORED = "trial_explored"
    EXPLORATORY = "exploratory"


class EvidenceTier(str, Enum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    INSUFFICIENT = "INSUFFICIENT"


class ExplanationBasis(BaseModel):
    graph_paths_count: int = 0
    literature_chunks: int = 0
    trial_count: int = 0
    evidence_tier: EvidenceTier = EvidenceTier.INSUFFICIENT
    is_known_indication: bool = False


class StructuredExplanation(BaseModel):
    structured_summary: str
    plain_language_summary: str
    uncertainty_statement: str
    basis: ExplanationBasis
