from typing import List, Dict
from config.ra_therapies import get_known_indications as get_ra_known, get_adjacent_therapies as get_ra_adj
from config.adjacent_therapies import get_known_indications, get_adjacent_therapies, get_disease_name

DISEASE_MAP = {
    "C0003873": {"name": "rheumatoid arthritis", "therapies_fn": None},
    "C0024141": {"name": "systemic lupus erythematosus", "therapies_fn": None},
    "C0395076": {"name": "psoriatic arthritis", "therapies_fn": None},
    "C0036075": {"name": "sjogren syndrome", "therapies_fn": None},
}

def build_gold_standard(cui: str = "C0003873") -> List[Dict]:
    if cui == "C0003873":
        gold = []
        for name in sorted(get_ra_known()):
            gold.append({"drug_name": name, "disease": "rheumatoid arthritis", "disease_cui": "C0003873", "category": "known_indication"})
        for name in sorted(get_ra_adj()):
            gold.append({"drug_name": name, "disease": "rheumatoid arthritis", "disease_cui": "C0003873", "category": "adjacent_offlabel"})
        return gold
    else:
        gold = []
        disease_name = get_disease_name(cui)
        for name in sorted(get_known_indications(cui)):
            gold.append({"drug_name": name, "disease": disease_name, "disease_cui": cui, "category": "known_indication"})
        for name in sorted(get_adjacent_therapies(cui)):
            gold.append({"drug_name": name, "disease": disease_name, "disease_cui": cui, "category": "adjacent_offlabel"})
        return gold

def build_ra_gold_standard() -> List[Dict]:
    return build_gold_standard("C0003873")
