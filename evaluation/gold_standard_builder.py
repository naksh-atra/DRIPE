"""
Gold standard builder for DRIPE v2 evaluation.
Constructs known-therapy lists from public sources.
"""
from typing import List, Dict

# Per-disease gold standards (therapy names in lowercase)
DISEASE_GOLD_STANDARDS = {
    "C0003873": {  # RA
        "methotrexate", "adalimumab", "etanercept", "infliximab", "rituximab",
        "tocilizumab", "baricitinib", "tofacitinib", "abatacept", "sulfasalazine",
        "leflunomide", "hydroxychloroquine", "certolizumab", "golimumab", "sarilumab",
        "upadacitinib", "filgotinib", "anakinra", "prednisone", "methylprednisolone",
        "cyclosporine", "azathioprine", "penicillamine", "mycophenolate",
    },
    "C0024141": {  # SLE
        "hydroxychloroquine", "belimumab", "mycophenolate mofetil",
        "cyclophosphamide", "azathioprine", "anifrolumab", "tacrolimus",
        "methotrexate", "rituximab", "prednisone", "methylprednisolone",
        "leflunomide", "abatacept",
    },
    "C0395076": {  # PsA
        "methotrexate", "adalimumab", "etanercept", "infliximab", "secukinumab",
        "ixekizumab", "ustekinumab", "apremilast", "certolizumab", "golimumab",
        "tofacitinib", "upadacitinib", "brodalumab", "risankizumab",
        "bimekizumab", "guselkumab", "tildrakizumab", "certolizumab pegol",
        "leflunomide", "sulfasalazine", "cyclosporine",
    },
    "C0036075": {  # Sjogren
        "pilocarpine", "cevimeline",
        "hydroxychloroquine", "rituximab", "belimumab",
        "methotrexate", "leflunomide", "azathioprine",
        "mycophenolate mofetil", "cyclophosphamide",
        "prednisone", "methylprednisolone",
        "abatacept", "anakinra",
    },
}


def build_gold_standard(disease_cui: str) -> List[Dict]:
    """Build gold standard for a given disease CUI."""
    drug_names = DISEASE_GOLD_STANDARDS.get(disease_cui, set())
    disease_name_map = {
        "C0003873": "rheumatoid arthritis",
        "C0024141": "systemic lupus erythematosus",
        "C0395076": "psoriatic arthritis",
        "C0036075": "sjogren syndrome",
    }
    disease = disease_name_map.get(disease_cui, "unknown")
    gold = []
    for drug in sorted(drug_names):
        gold.append({
            "drug_name": drug,
            "disease": disease,
            "disease_cui": disease_cui,
            "category": "known_indication",
        })
    return gold


def build_ra_gold_standard() -> List[Dict]:
    """Build gold standard of known RA therapies (kept for backward compat)."""
    return build_gold_standard("C0003873")
