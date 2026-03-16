from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class RelationshipRecord(BaseModel):
    source_id: str
    source_type: str  # drug, protein, gene, disease, pathway
    target_id: str
    target_type: str
    relationship_type: str  # inhibits, activates, associated_with, expressed_in, treats, causes, interacts_with
    confidence: float = Field(ge=0.0, le=1.0)
    source_db: str
    evidence_year: Optional[int] = None
    pmid: Optional[str] = None
    doi: Optional[str] = None

def format_record(data: Dict[str, Any]) -> RelationshipRecord:
    """Validator for intermediate representation"""
    return RelationshipRecord(**data)
