def compute_edge_confidence(
    base_confidence: float,
    independence_count: int,
    evidence_year: int,
    pubmed_count: int
) -> float:
    """
    Final Confidence Score Formula:
    Score = (Source Weight) * (Corroboration Bonus) * (Recency Decay) * (Replication Bonus)
    - Source Weight: Provided base_confidence (0.90, 0.75, or 0.55)
    - Corroboration: +0.05 per independent DB (max 0.20)
    - Recency: 1.0 (>=2015), 0.90 (2005-2014), 0.80 (<2005)
    - Replication: +0.03 per PubMed paper (max 0.15)
    """
    # 1. Corroboration Bonus
    corroboration_bonus = min((independence_count - 1) * 0.05, 0.20) if independence_count > 1 else 0.0
    
    # 2. Recency Decay
    if evidence_year >= 2015:
        recency_factor = 1.0
    elif evidence_year >= 2005:
        recency_factor = 0.90
    else:
        recency_factor = 0.80
        
    # 3. Replication Bonus
    replication_bonus = min(pubmed_count * 0.03, 0.15)
    
    # Calculation
    final_score = base_confidence * (1 + corroboration_bonus) * recency_factor * (1 + replication_bonus)
    
    # Clip to maximum of 0.99
    return min(final_score, 0.99)

def filter_edges(confidence: float) -> str:
    """
    Thresholds:
    - < 0.30: DELETE (REMOVE)
    - 0.30 - 0.50: LOW_CONFIDENCE
    - > 0.50: RETAINED
    """
    if confidence < 0.30:
        return "REMOVE"
    elif confidence <= 0.50:
        return "LOW_CONFIDENCE"
    return "RETAINED"
