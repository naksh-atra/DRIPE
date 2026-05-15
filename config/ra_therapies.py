"""
Canonical RA therapy registry.
Curated list of known RA therapies with target mappings.
"""
from typing import Dict, List

THERAPIES = [
    # === Conventional DMARDs ===
    {"name": "methotrexate", "chembl_id": "CHEMBL34259", "mechanism": "DHFR inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL2027", "name": "DHFR", "evidence": "approved_ra"}]},

    {"name": "sulfasalazine", "chembl_id": "CHEMBL421", "mechanism": "Anti-inflammatory", "category": "known_indication",
     "targets": [{"id": "CHEMBL224", "name": "COX2", "evidence": "literature"}, {"id": "CHEMBL217", "name": "COX1", "evidence": "literature"}]},

    {"name": "leflunomide", "chembl_id": "CHEMBL960", "mechanism": "DHODH inhibitor", "category": "known_indication",
     "targets": []},

    {"name": "hydroxychloroquine", "chembl_id": "CHEMBL1535", "mechanism": "TLR antagonist", "category": "known_indication",
     "targets": []},

    # === Corticosteroids ===
    {"name": "prednisone", "chembl_id": "CHEMBL635", "mechanism": "Glucocorticoid receptor agonist", "category": "known_indication",
     "targets": []},

    {"name": "methylprednisolone", "chembl_id": "CHEMBL650", "mechanism": "Glucocorticoid receptor agonist", "category": "known_indication",
     "targets": []},

    # === JAK inhibitors ===
    {"name": "baricitinib", "chembl_id": "CHEMBL2105759", "mechanism": "JAK1/JAK2 inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL2103830", "name": "JAK1", "evidence": "approved_ra"}, {"id": "CHEMBL2146302", "name": "JAK2", "evidence": "approved_ra"}]},

    {"name": "tofacitinib", "chembl_id": "CHEMBL221959", "mechanism": "JAK1/JAK2/JAK3 inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL2103830", "name": "JAK1", "evidence": "approved_ra"}, {"id": "CHEMBL2146302", "name": "JAK2", "evidence": "approved_ra"}, {"id": "CHEMBL2146303", "name": "JAK3", "evidence": "approved_ra"}]},

    {"name": "upadacitinib", "chembl_id": "CHEMBL3622821", "mechanism": "JAK1 inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL2103830", "name": "JAK1", "evidence": "approved_ra"}]},

    {"name": "filgotinib", "chembl_id": "CHEMBL3301607", "mechanism": "JAK1 inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL2103830", "name": "JAK1", "evidence": "approved_ra"}]},

    # === TNF inhibitors ===
    {"name": "adalimumab", "chembl_id": "", "mechanism": "TNF inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL244", "name": "TNF", "evidence": "approved_ra"}]},

    {"name": "etanercept", "chembl_id": "", "mechanism": "TNF inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL244", "name": "TNF", "evidence": "approved_ra"}]},

    {"name": "infliximab", "chembl_id": "", "mechanism": "TNF inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL244", "name": "TNF", "evidence": "approved_ra"}]},

    {"name": "certolizumab", "chembl_id": "", "mechanism": "TNF inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL244", "name": "TNF", "evidence": "approved_ra"}]},

    {"name": "golimumab", "chembl_id": "", "mechanism": "TNF inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL244", "name": "TNF", "evidence": "approved_ra"}]},

    # === IL-6 inhibitors ===
    {"name": "tocilizumab", "chembl_id": "", "mechanism": "IL6R inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL3399910", "name": "IL6R", "evidence": "approved_ra"}]},

    {"name": "sarilumab", "chembl_id": "", "mechanism": "IL6R inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL3399910", "name": "IL6R", "evidence": "approved_ra"}]},

    # === CD20 inhibitor ===
    {"name": "rituximab", "chembl_id": "", "mechanism": "CD20 inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL3712", "name": "CD20", "evidence": "approved_ra"}]},

    # === CTLA4 modulator ===
    {"name": "abatacept", "chembl_id": "", "mechanism": "CTLA4 modulator", "category": "known_indication",
     "targets": [{"id": "CHEMBL3522", "name": "CTLA4", "evidence": "approved_ra"}]},

    # === IL-1 inhibitor ===
    {"name": "anakinra", "chembl_id": "", "mechanism": "IL1R antagonist", "category": "known_indication",
     "targets": [{"id": "CHEMBL325", "name": "IL1B", "evidence": "approved_ra"}]},

    # === NSAIDs (adjacent use in RA) ===
    {"name": "celecoxib", "chembl_id": "CHEMBL118", "mechanism": "COX2 inhibitor", "category": "adjacent_offlabel",
     "targets": [{"id": "CHEMBL224", "name": "COX2", "evidence": "literature"}]},

    {"name": "ibuprofen", "chembl_id": "CHEMBL521", "mechanism": "COX1/COX2 inhibitor", "category": "adjacent_offlabel",
     "targets": [{"id": "CHEMBL217", "name": "COX1", "evidence": "literature"}, {"id": "CHEMBL224", "name": "COX2", "evidence": "literature"}]},

    {"name": "naproxen", "chembl_id": "CHEMBL154", "mechanism": "COX1/COX2 inhibitor", "category": "adjacent_offlabel",
     "targets": [{"id": "CHEMBL217", "name": "COX1", "evidence": "literature"}, {"id": "CHEMBL224", "name": "COX2", "evidence": "literature"}]},
]


def get_all() -> List[Dict]:
    return THERAPIES


def get_chembl_id_map() -> Dict[str, str]:
    return {t["name"]: t["chembl_id"] for t in THERAPIES if t["chembl_id"]}


def get_known_indications() -> Dict[str, str]:
    return {t["name"]: t["chembl_id"] for t in THERAPIES if t["category"] == "known_indication"}


def get_adjacent_therapies() -> Dict[str, str]:
    return {t["name"]: t["chembl_id"] for t in THERAPIES if t["category"] == "adjacent_offlabel"}
