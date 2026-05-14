# Deliverable B: Data and Graph Spec

## Status: Design Decision — 2026-03-22

---

## 1. Minimum Viable Data Sources

### Required for MVP

| Source | Data Type | Role in Pipeline | Priority |
|--------|-----------|------------------|----------|
| **ChEMBL** (via existing connector) | Drug-target binding affinities (pChEMBL ≥ 6.0) | Build Drug→Target edges | P0 — must have |
| **ClinicalTrials.gov** (via existing connector) | Interventional RA trials, phase, outcomes | Build Drug→Trial→Disease edges, evidence score | P0 — must have |
| **PubMed** (via existing connector) | Abstracts for drug-disease pairs | Populate FAISS index, evidence retrieval | P0 — must have |
| **OpenFDA** (via existing connector) | Adverse event reports | Build Drug→AdverseEvent edges, safety signals | P1 — important |
| **DrugBank** (new connector needed) | Drug approval status, mechanism of action | Drug metadata, novelty classification | P1 — important |
| **RTX-KG2** (via skeleton loader) | Pre-merged biomedical KG | Graph density, path diversity | P2 — future |

### What this means for the MVP graph
- Target size: ~500-1,000 nodes, ~2,000-5,000 edges for MVP
- Not the full ChEMBL database (~2M compounds)
- Not the full ClinicalTrials.gov registry
- Only the RA-relevant subset

---

## 2. Graph Node and Edge Schema

### Node types

| Node Type | Properties | Example | Source |
|-----------|------------|---------|--------|
| `Drug` | entity_id (ChEMBL ID), name, approval_status, mechanism | "CHEMBL1201580" (baricitinib) | ChEMBL, DrugBank |
| `Target` | entity_id (UniProt ID), name, gene_symbol, target_type | "P51681" (JAK1) | ChEMBL |
| `Pathway` | entity_id (Reactome/KEGG ID), name | "R-HSA-9020559" (JAK-STAT signaling) | Reactome (external) |
| `Disease` | entity_id (UMLS CUI), name, ontology_source | "C0003873" (RA) | Curated |
| `Trial` | entity_id (NCT ID), title, phase, status, conditions | "NCT01039559" | ClinicalTrials.gov |
| `AdverseEvent` | entity_id (MedDRA PT code), term | "ME10007642" (infection) | OpenFDA |

### Edge types

| Edge Type | Source → Target | Properties | Confidence Basis | MVP Priority |
|-----------|----------------|------------|------------------|--------------|
| `TARGETS` | Drug → Target | confidence, source_db, pmid, action_type (inhibitor/agonist/antagonist) | pChEMBL | Required |
| `INDICATES` | Drug → Disease | confidence, source_db, approval_status, phase | FDA approval | Required |
| `TRIAL_INVESTIGATES` | Drug → Trial | confidence, phase, status, nct_id | Trial registry | Required |
| `TRIAL_CONDITION` | Trial → Disease | --- | Trial conditions field | Required |
| `ASSOCIATED_WITH` | Target → Disease | confidence, source_db, pmid, evidence_type (genetic/expression/... | DisGeNET/OpenTargets | Required |
| `PARTICIPATES_IN` | Target → Pathway | confidence, source_db | Reactome/KEGG | Preferred |
| `PATHWAY_DYSREGULATED` | Pathway → Disease | confidence, source_db, pmid | Literature | Preferred |
| `CAUSES` | Drug → AdverseEvent | confidence, source_db, frequency, severity | OpenFDA | Optional (P1) |
| `ADVERSE_EVENT_LINK` | AdverseEvent → Disease | confidence (inferred) | --- | Optional (P2) |

### Provenance fields (every edge must have)

| Field | Type | Example | Required |
|-------|------|---------|----------|
| `source_db` | string | "chembl", "clinicaltrials", "drugbank" | Yes |
| `confidence` | float (0-1) | 0.85 | Yes |
| `pmid` | string | "34873336" | Where available |
| `evidence_year` | integer | 2023 | Yes |
| `source_record_id` | string | "CHEMBL123456" | Yes |

---

## 3. Disease-Program Filtering Strategy

### How it works in Neo4j
When an RA query arrives:

```cypher
// Step 1: Identify the primary disease node
MATCH (d:Disease {entity_id: "C0003873"})

// Step 2: Find drugs connected via any path
// but prefer paths that stay within the RA-relevant subgraph
MATCH path = (drug:Drug)-[*1..3]-(disease:Disease {entity_id: "C0003873"})
WHERE ALL(node IN nodes(path) WHERE node.entity_type IN ['Drug', 'Target', 'Pathway', 'Disease', 'Trial'])
RETURN drug, path
```

### Adjacency disease inclusion
- When querying RA, also search for edges involving SLE, PsA, Sjogren
- Score adjacency signals separately (not mixed with primary disease scores)
- Label adjacency signals with their source disease

---

## 4. Path Types to Support (Ordered by Priority for MVP)

| Priority | Path Type | Example | Explanation Value |
|----------|-----------|---------|-------------------|
| P0 | Drug → Target → Disease | Baricitinib → JAK1 → RA | Core mechanism path |
| P0 | Drug → Trial → Disease | Tocilizumab → NCT01039559 → RA | Trial evidence path |
| P1 | Drug → Target → Pathway → Disease | Adalimumab → TNF-α → NF-κB → RA | Mechanistic depth |
| P2 | Drug → AdverseEvent ↔ Disease | Methotrexate → Hepatotoxicity ↔ RA | Safety context |
| P2 | Drug → Target → Disease ← Target₂ ← Drug₂ | Shared target → cross-drug signal | Adjacency discovery |

---

## 5. `supporting_paths` Output Object Design

```json
{
  "supporting_paths": [
    {
      "path_type": "Drug-Target-Disease",
      "path_string": "Baricitinib → JAK1 → Rheumatoid Arthritis",
      "nodes": [
        {"id": "CHEMBL1201580", "name": "Baricitinib", "type": "Drug"},
        {"id": "P51681", "name": "JAK1", "type": "Target"},
        {"id": "C0003873", "name": "Rheumatoid Arthritis", "type": "Disease"}
      ],
      "edges": [
        {"source": "CHEMBL1201580", "target": "P51681", "type": "TARGETS", "confidence": 0.88, "source_db": "chembl"},
        {"source": "P51681", "target": "C0003873", "type": "ASSOCIATED_WITH", "confidence": 0.72, "source_db": "opentargets"}
      ],
      "path_confidence": 0.80,
      "provenance": ["chembl", "opentargets"]
    }
  ]
}
```

---

## 6. `coverage_report` Output Object Design

```json
{
  "coverage_report": {
    "primary_disease": "rheumatoid arthritis",
    "graph_density_note": "Current RA subgraph contains X drugs, Y targets, and Z edges. Coverage is [HIGH / MODERATE / LOW] relative to known RA pharmacology.",
    "literature_density_note": "PubMed index contains X abstracts for RA drug-disease pairs. Y% of candidates have at least one supporting literature chunk.",
    "trial_evidence_note": "X clinical trials for RA are indexed. Y% of candidates have trial evidence.",
    "known_limitations": [
      "Graph does not include pathway nodes yet — path explanations end at Target.",
      "FAISS index contains only 16 chunks — retrieval coverage is minimal.",
      "No contradiction signals are indexed — only supporting evidence is shown.",
      "Adjacency disease signals are exploratory — not validated for SLE/PsA/Sjogren."
    ]
  }
}
```

---

## 7. Mandatory vs Optional for MVP

| Component | MVP | Later |
|-----------|-----|-------|
| Drug node | Required | — |
| Target node | Required | — |
| Disease node | Required | — |
| Pathway node | Preferred | Required for depth |
| Trial node | Required | — |
| AdverseEvent node | Optional | Required |
| Drug→Target | Required | — |
| Drug→Disease | Required (known indications) | — |
| Drug→Trial | Required | — |
| Target→Disease | Required | — |
| Target→Pathway | Preferred | Required |
| Pathway→Disease | Preferred | Required |
| Provenance on edges | Required | — |
| Disease-program filtering | Required | — |
