"""
Query schemas for DRIPE v2.
Defines the input contract and query normalization results.
"""
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class QueryStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED_UNSUPPORTED_DISEASE = "unsupported_disease"
    REJECTED_PATIENT_QUERY = "patient_specific"
    REJECTED_TREATMENT_QUERY = "treatment_advice"


class QueryMode(str, Enum):
    STANDARD = "standard"
    EVALUATION = "evaluation"


class QueryRequest(BaseModel):
    disease_input: str
    query_mode: QueryMode = QueryMode.STANDARD


class QueryResult(BaseModel):
    disease_input: str
    canonical_disease_id: Optional[str] = None
    query_status: QueryStatus
    rejection_reason: Optional[str] = None
    adjacency_diseases: List[str] = Field(default_factory=list)
