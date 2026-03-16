import math

def calculate_equity_weight(
    daly_count: float,
    global_max_daly: float,
    approved_treatment_count: int,
    funding_index: float
) -> float:
    """
    Equity Weight = (DALY / MaxDALY) * (1 / (Treatments + 1)) * (1 / log(Funding + 2))
    """
    term1 = daly_count / global_max_daly
    term2 = 1.0 / (approved_treatment_count + 1)
    term3 = 1.0 / math.log(funding_index + 2)
    
    weight = term1 * term2 * term3
    
    # Cap at 0.5
    return min(weight, 0.5)

def rank_hypotheses(
    gnn_score: float,
    lit_score: float,
    path_conf: float,
    equity_weight: float
) -> float:
    """
    Final Score = (gnn*0.4 + lit*0.3 + path*0.3) * (1 + equity_weight)
    """
    base_score = (gnn_score * 0.4) + (lit_score * 0.3) + (path_conf * 0.3)
    return base_score * (1 + equity_weight)
