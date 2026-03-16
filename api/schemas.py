from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime

class CoverageReport(BaseModel):
    completeness_tier: str  # LOW, MEDIUM, HIGH
    gene_association_count: int
    protein_interaction_count: int
    pubmed_paper_count: int
    trial_count: int
    sparse_edges: List[str]

class HypothesisCandidate(BaseModel):
    rank: int
    drug_name: str
    drug_id: str
    approval_status: str
    confidence_tier: str  # STRONG_EVIDENCE, MODERATE, EXPLORATORY
    gnn_similarity_score: float
    graph_path_confidence: float
    literature_support_count: int
    equity_weight: float
    reasoning_chain: List[Dict]
    retrieved_literature: List[Dict]
    safety_flags: List[str]
    next_steps: str

class QueryResponse(BaseModel):
    query_disease: str
    query_timestamp: datetime = Field(default_factory=datetime.utcnow)
    graph_version: str
    coverage_report: CoverageReport
    candidates: List[HypothesisCandidate]
    disclaimer: str
    timeout_flag: bool = False

class QueryRequest(BaseModel):
    disease: str
    max_candidates: Optional[int] = 10
    min_confidence: Optional[float] = 0.50
    include_exploratory: Optional[bool] = False
