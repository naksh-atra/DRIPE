"""Batch-update Drug nodes with names from ChEMBL API."""
import asyncio, httpx, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()
from graph.graph_builder import GraphEngine

CHEMBL_BASE = "https://www.ebi.ac.uk/chembl/api/data/molecule"
CONCURRENCY = 5

sem = asyncio.Semaphore(CONCURRENCY)

async def fetch_name(client, cid):
    async with sem:
        try:
            r = await client.get(f"{CHEMBL_BASE}/{cid}.json", timeout=15)
            if r.status_code != 200:
                return cid, ""
            data = r.json()
            name = data.get("pref_name") or ""
            if not name and data.get("molecule_synonyms"):
                for s in data["molecule_synonyms"]:
                    if s.get("synonym") and s["synonym"].strip():
                        name = s["synonym"].strip()
                        break
            return cid, name
        except Exception:
            return cid, ""

async def main():
    g = GraphEngine()
    g.connect()
    drugs = g.run_cypher("MATCH (n:Entity {entity_type: 'Drug'}) WHERE n.name IS NULL RETURN n.entity_id AS eid")
    print(f"Found {len(drugs)} unnamed drugs")
    if not drugs:
        print("All drugs already named")
        g.close()
        return

    mapping = {}
    async with httpx.AsyncClient(timeout=30) as client:
        tasks = [fetch_name(client, row["eid"]) for row in drugs]
        results = await asyncio.gather(*tasks)

    for cid, name in results:
        if name:
            mapping[cid] = name
            g.run_cypher("MATCH (n:Entity {entity_id: $eid}) SET n.name = $name", {"eid": cid, "name": name})

    Path("data").mkdir(exist_ok=True)
    with open("data/chembl_id_name_map.json", "w") as f:
        json.dump(mapping, f, indent=2)

    print(f"Named {len(mapping)}/{len(drugs)} drugs")
    g.close()

if __name__ == "__main__":
    asyncio.run(main())
