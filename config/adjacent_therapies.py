from typing import Dict, List

SLE_THERAPIES = [
    {"name": "hydroxychloroquine", "chembl_id": "CHEMBL1535", "mechanism": "TLR antagonist", "category": "known_indication",
     "targets": []},
    {"name": "belimumab", "chembl_id": "", "mechanism": "BLyS inhibitor", "category": "known_indication",
     "targets": []},
    {"name": "mycophenolate mofetil", "chembl_id": "", "mechanism": "IMPDH inhibitor", "category": "known_indication",
     "targets": []},
    {"name": "cyclophosphamide", "chembl_id": "", "mechanism": "Alkylating agent", "category": "known_indication",
     "targets": []},
    {"name": "azathioprine", "chembl_id": "", "mechanism": "Purine analogue", "category": "known_indication",
     "targets": []},
    {"name": "methotrexate", "chembl_id": "CHEMBL34259", "mechanism": "DHFR inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL2027", "name": "DHFR", "evidence": "literature"}]},
    {"name": "rituximab", "chembl_id": "", "mechanism": "CD20 inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL3712", "name": "CD20", "evidence": "approved_sle"}]},
    {"name": "prednisone", "chembl_id": "CHEMBL635", "mechanism": "Glucocorticoid receptor agonist", "category": "known_indication",
     "targets": []},
    {"name": "methylprednisolone", "chembl_id": "CHEMBL650", "mechanism": "Glucocorticoid receptor agonist", "category": "known_indication",
     "targets": []},
    {"name": "anifrolumab", "chembl_id": "", "mechanism": "IFNAR1 inhibitor", "category": "known_indication",
     "targets": []},
    {"name": "tacrolimus", "chembl_id": "", "mechanism": "Calcineurin inhibitor", "category": "known_indication",
     "targets": []},
    {"name": "leflunomide", "chembl_id": "CHEMBL960", "mechanism": "DHODH inhibitor", "category": "known_indication",
     "targets": []},
    {"name": "abatacept", "chembl_id": "", "mechanism": "CTLA4 modulator", "category": "known_indication",
     "targets": [{"id": "CHEMBL3522", "name": "CTLA4", "evidence": "literature"}]},
]

PsA_THERAPIES = [
    {"name": "adalimumab", "chembl_id": "", "mechanism": "TNF inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL244", "name": "TNF", "evidence": "approved_psa"}]},
    {"name": "etanercept", "chembl_id": "", "mechanism": "TNF inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL244", "name": "TNF", "evidence": "approved_psa"}]},
    {"name": "infliximab", "chembl_id": "", "mechanism": "TNF inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL244", "name": "TNF", "evidence": "approved_psa"}]},
    {"name": "certolizumab", "chembl_id": "", "mechanism": "TNF inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL244", "name": "TNF", "evidence": "approved_psa"}]},
    {"name": "golimumab", "chembl_id": "", "mechanism": "TNF inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL244", "name": "TNF", "evidence": "approved_psa"}]},
    {"name": "secukinumab", "chembl_id": "", "mechanism": "IL17A inhibitor", "category": "known_indication",
     "targets": []},
    {"name": "ixekizumab", "chembl_id": "", "mechanism": "IL17A inhibitor", "category": "known_indication",
     "targets": []},
    {"name": "brodalumab", "chembl_id": "", "mechanism": "IL17RA inhibitor", "category": "known_indication",
     "targets": []},
    {"name": "ustekinumab", "chembl_id": "", "mechanism": "IL12/IL23 inhibitor", "category": "known_indication",
     "targets": []},
    {"name": "guselkumab", "chembl_id": "", "mechanism": "IL23 inhibitor", "category": "known_indication",
     "targets": []},
    {"name": "risankizumab", "chembl_id": "", "mechanism": "IL23 inhibitor", "category": "known_indication",
     "targets": []},
    {"name": "tofacitinib", "chembl_id": "CHEMBL221959", "mechanism": "JAK1/JAK2/JAK3 inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL2103830", "name": "JAK1", "evidence": "approved_psa"}, {"id": "CHEMBL2146302", "name": "JAK2", "evidence": "approved_psa"}, {"id": "CHEMBL2146303", "name": "JAK3", "evidence": "approved_psa"}]},
    {"name": "upadacitinib", "chembl_id": "CHEMBL3622821", "mechanism": "JAK1 inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL2103830", "name": "JAK1", "evidence": "approved_psa"}]},
    {"name": "methotrexate", "chembl_id": "CHEMBL34259", "mechanism": "DHFR inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL2027", "name": "DHFR", "evidence": "literature"}]},
    {"name": "leflunomide", "chembl_id": "CHEMBL960", "mechanism": "DHODH inhibitor", "category": "known_indication",
     "targets": []},
    {"name": "sulfasalazine", "chembl_id": "CHEMBL421", "mechanism": "Anti-inflammatory", "category": "known_indication",
     "targets": [{"id": "CHEMBL224", "name": "COX2", "evidence": "literature"}, {"id": "CHEMBL217", "name": "COX1", "evidence": "literature"}]},
    {"name": "apremilast", "chembl_id": "", "mechanism": "PDE4 inhibitor", "category": "known_indication",
     "targets": []},
    {"name": "celecoxib", "chembl_id": "CHEMBL118", "mechanism": "COX2 inhibitor", "category": "adjacent_offlabel",
     "targets": [{"id": "CHEMBL224", "name": "COX2", "evidence": "literature"}]},
    {"name": "ibuprofen", "chembl_id": "CHEMBL521", "mechanism": "COX1/COX2 inhibitor", "category": "adjacent_offlabel",
     "targets": [{"id": "CHEMBL217", "name": "COX1", "evidence": "literature"}, {"id": "CHEMBL224", "name": "COX2", "evidence": "literature"}]},
    {"name": "naproxen", "chembl_id": "CHEMBL154", "mechanism": "COX1/COX2 inhibitor", "category": "adjacent_offlabel",
     "targets": [{"id": "CHEMBL217", "name": "COX1", "evidence": "literature"}, {"id": "CHEMBL224", "name": "COX2", "evidence": "literature"}]},
    {"name": "prednisone", "chembl_id": "CHEMBL635", "mechanism": "Glucocorticoid receptor agonist", "category": "known_indication",
     "targets": []},
]

SJOGREN_THERAPIES = [
    {"name": "hydroxychloroquine", "chembl_id": "CHEMBL1535", "mechanism": "TLR antagonist", "category": "known_indication",
     "targets": []},
    {"name": "pilocarpine", "chembl_id": "", "mechanism": "Muscarinic agonist", "category": "known_indication",
     "targets": []},
    {"name": "cevimeline", "chembl_id": "", "mechanism": "Muscarinic agonist", "category": "known_indication",
     "targets": []},
    {"name": "methotrexate", "chembl_id": "CHEMBL34259", "mechanism": "DHFR inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL2027", "name": "DHFR", "evidence": "literature"}]},
    {"name": "leflunomide", "chembl_id": "CHEMBL960", "mechanism": "DHODH inhibitor", "category": "known_indication",
     "targets": []},
    {"name": "rituximab", "chembl_id": "", "mechanism": "CD20 inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL3712", "name": "CD20", "evidence": "literature"}]},
    {"name": "prednisone", "chembl_id": "CHEMBL635", "mechanism": "Glucocorticoid receptor agonist", "category": "known_indication",
     "targets": []},
    {"name": "methylprednisolone", "chembl_id": "CHEMBL650", "mechanism": "Glucocorticoid receptor agonist", "category": "known_indication",
     "targets": []},
    {"name": "abatacept", "chembl_id": "", "mechanism": "CTLA4 modulator", "category": "known_indication",
     "targets": [{"id": "CHEMBL3522", "name": "CTLA4", "evidence": "literature"}]},
    {"name": "belimumab", "chembl_id": "", "mechanism": "BLyS inhibitor", "category": "known_indication",
     "targets": []},
    {"name": "anifrolumab", "chembl_id": "", "mechanism": "IFNAR1 inhibitor", "category": "known_indication",
     "targets": []},
    {"name": "tofacitinib", "chembl_id": "CHEMBL221959", "mechanism": "JAK1/JAK2/JAK3 inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL2103830", "name": "JAK1", "evidence": "literature"}, {"id": "CHEMBL2146302", "name": "JAK2", "evidence": "literature"}, {"id": "CHEMBL2146303", "name": "JAK3", "evidence": "literature"}]},
    {"name": "baricitinib", "chembl_id": "CHEMBL2105759", "mechanism": "JAK1/JAK2 inhibitor", "category": "known_indication",
     "targets": [{"id": "CHEMBL2103830", "name": "JAK1", "evidence": "literature"}, {"id": "CHEMBL2146302", "name": "JAK2", "evidence": "literature"}]},
    {"name": "azathioprine", "chembl_id": "", "mechanism": "Purine analogue", "category": "known_indication",
     "targets": []},
    {"name": "cyclophosphamide", "chembl_id": "", "mechanism": "Alkylating agent", "category": "known_indication",
     "targets": []},
    {"name": "mycophenolate mofetil", "chembl_id": "", "mechanism": "IMPDH inhibitor", "category": "known_indication",
     "targets": []},
]

THERAPY_REGISTRY = {
    "C0024141": {"name": "systemic lupus erythematosus", "therapies": SLE_THERAPIES},
    "C0395076": {"name": "psoriatic arthritis", "therapies": PsA_THERAPIES},
    "C0036075": {"name": "sjogren syndrome", "therapies": SJOGREN_THERAPIES},
}

def get_therapies(cui: str) -> List[Dict]:
    return THERAPY_REGISTRY.get(cui, {}).get("therapies", [])

def get_known_indications(cui: str) -> Dict[str, str]:
    return {t["name"]: t["chembl_id"] for t in get_therapies(cui) if t["category"] == "known_indication"}

def get_adjacent_therapies(cui: str) -> Dict[str, str]:
    return {t["name"]: t["chembl_id"] for t in get_therapies(cui) if t["category"] == "adjacent_offlabel"}

def get_chembl_id_map(cui: str) -> Dict[str, str]:
    return {t["name"]: t["chembl_id"] for t in get_therapies(cui) if t["chembl_id"]}

def get_disease_name(cui: str) -> str:
    return THERAPY_REGISTRY.get(cui, {}).get("name", "")
