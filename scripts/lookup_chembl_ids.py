"""Look up ChEMBL IDs for known RA therapies."""
import requests, json, time

DRUGS = [
    "methotrexate", "baricitinib", "tofacitinib", "upadacitinib", "filgotinib",
    "sulfasalazine", "leflunomide", "hydroxychloroquine", "prednisone",
    "methylprednisolone", "cyclosporine", "azathioprine", "celecoxib",
    "ibuprofen", "naproxen", "aspirin",
]

results = {}
for name in DRUGS:
    try:
        r = requests.get(
            f"https://www.ebi.ac.uk/chembl/api/data/molecule?pref_name__iexact={name}&format=json",
            timeout=15
        )
        if r.status_code == 200:
            molecules = r.json().get("molecules", [])
            if molecules:
                m = molecules[0]
                results[name] = {
                    "chembl_id": m["molecule_chembl_id"],
                    "pref_name": m.get("pref_name", name),
                }
                print(f"  {name:20s} -> {results[name]['chembl_id']}")
            else:
                print(f"  {name:20s} -> NOT FOUND")
        time.sleep(0.3)
    except Exception as e:
        print(f"  {name:20s} -> ERROR: {e}")

with open("data/ra_drug_chembl_ids.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved {len(results)} mappings")
