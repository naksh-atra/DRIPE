# Deliverable A: Disease Program Decision Memo

## Status: Design Decision — 2026-03-22

---

## 1. Recommendation

**Rheumatoid arthritis (RA) as the primary MVP disease.**

Adjacency set for graph context:
- Systemic lupus erythematosus (SLE)
- Psoriatic arthritis (PsA)
- Sjogren syndrome / Sjogren disease

No other autoimmune diseases should be queryable in the MVP. The adjacency set exists only to enrich graph paths and cross-disease reasoning, not as independently supported query targets.

---

## 2. Rationale for RA

### 2.1 Public data availability
RA has the richest public data density among autoimmune diseases:
- **ChEMBL:** Thousands of documented drug-target interactions for RA-related targets (TNF, IL-6, JAK, CD20)
- **ClinicalTrials.gov:** 3,000+ interventional trials for RA (vs. ~1,500 for SLE, ~800 for PsA)
- **PubMed:** Dense literature with clearly defined MeSH headings, drug-specific subheadings
- **OpenFDA:** High adverse-event reporting volume due to widespread use of RA biologics

### 2.2 Graph structure advantages
RA naturally produces a variety of informative graph path types:
- Drug → Target → Disease (JAK inhibitors → JAK kinases → RA)
- Drug → Target → Pathway → Disease (TNF inhibitors → NF-κB pathway → inflammatory cascade → RA)
- Drug → Trial → Disease (any drug with completed Phase III or IV RA trial)
- Drug → Adverse Event ↔ Disease-context relevance (infection risk with biologics)

### 2.3 Evaluation tractability
RA has a well-characterized known-therapy landscape:
- ~20+ FDA-approved biologics and DMARDs
- Clear first-line vs. second-line therapy stratification
- Known off-label and adjacent signals (e.g., baricitinib for COVID-19, tocilizumab for cytokine release syndrome)
- Multiple active comparator trials that establish ground truth for ranking evaluation

### 2.4 Explanation interpretability
RA pathomechanisms are better understood and more teachable than many autoimmune diseases:
- TNF-α, IL-6, JAK-STAT pathways are well-characterized
- Drug mechanisms of action are relatively clean (target inhibition, receptor blockade)
- Clinical trial endpoints (ACR20/50/70, DAS28) are standardized and well-documented

---

## 3. Alternative Considered: Psoriatic Arthritis

### Why not PsA as primary?
- Smaller trial evidence base (~800 interventional studies)
- More heterogeneous clinical presentation making canonical disease definition harder
- Fewer dedicated drug-approval patterns to use as evaluation ground truth
- Therapy landscape heavily overlaps with RA (TNF inhibitors, IL-17 inhibitors, JAK inhibitors), making separation of signals harder in a small graph

### What it offers
- Interesting mechanistic differentiation (IL-17/IL-23 axis vs. TNF/IL-6/JAK for RA)
- Potential for cross-disease evaluation (do RA-trained signals generalize to PsA?)
- Worth including as a secondary test target post-MVP

---

## 4. Disease Ontology Strategy

### Immediate plan
Use **UMLS CUI codes** as canonical IDs (already partially implemented in seed graph).

| Disease | UMLS CUI | Comments |
|---------|----------|----------|
| Rheumatoid arthritis | C0003873 | Well-mapped in UMLS |
| Systemic lupus erythematosus | C0024141 | |
| Psoriatic arthritis | C0395076 | May also use C0003872 (psoriatic arthropathies) |
| Sjogren syndrome | C0036075 | |

### Justification
- UMLS CUIs are free and publicly accessible
- ChEMBL and PubMed data already reference UMLS concepts
- Existing seed graph uses CUI-like identifiers; migration is straightforward
- No licensing restrictions (unlike SNOMED CT or ICD in some jurisdictions)

### Synonym handling
For the MVP, use a **canonical ID with a curated synonym table** rather than automated synonym expansion. A manually curated mapping of 10-15 known synonyms per disease (brand names, abbreviations, common misspellings) is safer than automated ontology expansion.

**Curated synonym list for RA:**
- "rheumatoid arthritis", "RA", "rheumatoid disease", "C0003873"
- Reject: "arthritis" (too broad), "osteoarthritis" (different disease entirely)

---

## 5. Query Input Strategy

### MVP decision: Accept only enumerated disease IDs + a curated shortlist of string synonyms

**Not recommended for MVP:** Free-text disease string normalization via LLM or ontology API.
- Risk of mapping "arthritis" → RA (incorrect)
- Risk of hallucinated ontology IDs
- Adds complexity without corresponding scientific benefit

**Recommended approach:**
1. Accept `canonical_disease_id` (UMLS CUI) as primary input
2. Accept a shortlist of predefined string aliases that map 1:1 to CUIs
3. Reject any disease not in the supported set with an explicit error message listing supported diseases
4. Document the exact allowed query schema in the API docs

---

## 6. MVP Query Constraints

| Property | Constraint |
|----------|-----------|
| Primary queryable disease | Rheumatoid arthritis (C0003873) |
| Adjacency diseases | SLE, PsA, Sjogren (graph context only) |
| Query form | `{"disease": "rheumatoid arthritis"}` or `{"disease": "C0003873"}` |
| Rejected queries | Free-form symptoms, patient descriptions, treatment requests |
| Default response | Ranked candidate list with evidence, scores, and explanations |
