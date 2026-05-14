# Structured Response: DRIPE MVP Design Reset

**Date:** 2026-03-22
**Answering:** Handoff document sections 1-12

---

## Section 1: Recommended Disease Scope

**Recommendation:** Rheumatoid arthritis (RA) as the single primary MVP disease.

**Adjacency set (graph context only, not queryable):**
- Systemic lupus erythematosus (SLE)
- Psoriatic arthritis (PsA)
- Sjogren syndrome

**Rationale:** RA has the richest public data density (ChEMBL targets, ClinicalTrials.gov trials, PubMed literature), the clearest known-therapy landscape for evaluation, and the most interpretable pathomechanisms for explanation generation.

**Full justification:** See `data/dripe_deliverable_A_disease_scope.md`

---

## Section 2: MVP Definition

> Given a supported disease (starting with rheumatoid arthritis), DRIPE returns a ranked shortlist of existing drugs along with graph-grounded evidence, retrieved literature/trial context, explicit uncertainty disclosures, and a constrained explanation of why the candidate may merit follow-up review.

### What the MVP answers
> "For this disease, which existing drugs are worth reviewing next, and why?"

### What the MVP does not answer
- Whether the drug works clinically
- Whether a patient should receive it
- Whether the hypothesis is novel
- Whether the system has discovered a therapeutic truth

---

## Section 3: Required Changes by Module

### 3.1 Guardrails — Keep, strengthen boundary
- Current state: Keyword-based intent classification, working for basic blocking
- MVP change: Add disease-program enum validation (reject any non-RA request with error listing supported diseases)
- Non-goal: Do not add LLM-based query classification for MVP

### 3.2 Graph Layer — Expand from seed to real subgraph
- Current state: 18 nodes, 12 edges (toy seed graph)
- MVP change: Populate RA-relevant subgraph from ChEMBL, ClinicalTrials.gov, PubMed
- Target: ~500-1,000 nodes, ~2,000-5,000 edges
- Schema: See `data/dripe_deliverable_B_graph_spec.md`

### 3.3 GNN/Ranking — Downgrade to secondary signal
- Current state: GAT is the primary (only) scoring mechanism
- MVP change: GNN becomes one of four scoring signals (15% weight). Path heuristic leads (40%)
- Baselines required: Common-neighbor, path-count, random
- Full spec: See `data/dripe_deliverable_C_ranking_spec.md`

### 3.4 Retrieval — Expand index, improve query construction
- Current state: FAISS with 16 chunks, generic query
- MVP change: Populate with 1,000+ PubMed abstracts + 200 trial records. Candidate-aware query construction
- Full spec: See `data/dripe_deliverable_D_retrieval_explanation_spec.md`

### 3.5 LLM — Downgrade from reasoning engine to evidence narrator
- Current state: Free-form chain-of-thought text generation
- MVP change: Constrained structured output (JSON). Only summarize supplied evidence. No speculation.
- Core principle: The graph and evidence do the reasoning; the LLM does bounded synthesis

### 3.6 Equity Ranker — Demote to metadata annotation
- Current state: Formula exists but not wired into pipeline
- MVP change: Compute equity weight as metadata field only. Do not use in composite ranking.
- Recommend: Retain as annotation field for secondary display. Revisit after biomedical validity is established.

---

## Section 4: Proposed Response Contract

See full schema in `data/dripe_deliverable_D_retrieval_explanation_spec.md`.

### Key changes from current response
1. **Explicit query/program scope block** — disease input, canonical ID, query status
2. **Coverage report with density notes** — graph, literature, trial density status + known limitations
3. **Multi-component scores** — graph_score, learned_score, evidence_score, composite_score
4. **Novelty bucket** — known_indication / adjacent_offlabel / trial_explored / exploratory
5. **Supporting paths as first-class objects** — path_type, nodes, edges, provenance
6. **Counter-evidence field** — sparse_support, contradictory_signal, known_failure
7. **Structured explanation** — structured_summary, plain_language_summary, uncertainty_statement

---

## Section 5: Evaluation Framework

Full spec in `data/dripe_deliverable_E_evaluation_spec.md`.

### Key commitments
1. **Gold standard constructed** from FDA labels, ClinicalTrials Phase III, PubMed reviews (~65 known RA signals)
2. **Two evaluation modes:** known-therapy recovery + novelty-aware (hide 30% of known links)
3. **Primary metrics:** Recall@10, Recall@20, MRR — always reported alongside baselines
4. **Manual review protocol:** Top-5 outputs checked for path grounding, literature match, explanation faithfulness
5. **Error taxonomy:** 9 categories including graph sparsity, hub-node bias, unsupported explanation, overly generic explanation

### MVP success criteria
- Recall@10 ≥ 30% (beats random)
- ≥ 80% of top-10 candidates have real graph paths
- ≥ 70% of top-5 explanations are faithful to evidence
- 100% of responses have non-empty uncertainty statements
- Zero clinical language violations

---

## Section 6: Risks and Non-Goals

Full risk register in `data/dripe_deliverable_F_risk_register.md`.

### Top 3 risks
1. **Graph is too small for meaningful GNN** (12 edges vs 5,000 needed) — GNN scores are essentially random
2. **Ollama is unstable** — crashes after repeated queries, 55s response time
3. **FAISS has 16 chunks** — retrieval evaluation is preliminary until index grows

### Non-goals (explicitly excluded from MVP)
- Multi-disease support (RA only)
- Patient-specific query handling
- Clinical recommendation
- Novelty discovery claims
- Equity-weighted ranking
- Any claim of biological validation

### What to say externally
> "DRIPE is a research platform that ranks drug repurposing hypotheses for rheumatoid arthritis by combining knowledge graph paths, literature retrieval, and a graph neural network, with an emphasis on inspectable outputs and uncertainty disclosure."

---

## Section 7: Decisions Requiring Human Approval

### Decision 1: Disease scope freeze
- **Options:** (a) RA only, (b) RA + adjacency context, (c) broader autoimmune set
- **Recommendation:** RA only + adjacency context
- **Trade-offs:** Narrower scope = deeper evaluation, but less impressive demos

### Decision 2: Query input format
- **Options:** (a) Enum-only (disease dropdown), (b) String + canonical ID, (c) Free text + normalization
- **Recommendation:** String + canonical ID (accept both "rheumatoid arthritis" and "C0003873")
- **Trade-offs:** Simpler implementation, but requires curated synonym list

### Decision 3: GNN role in ranking
- **Options:** (a) Lead scorer, (b) Secondary signal (15%), (c) Removed entirely
- **Recommendation:** Secondary signal (15%) — keep for pipeline continuity, do not overclaim
- **Trade-offs:** More complex composite score, but honest about current limitations

### Decision 4: Explanation format
- **Options:** (a) Free-form prose only, (b) Structured JSON only, (c) Both
- **Recommendation:** Structured JSON + short plain language summary (no free-form prose)
- **Trade-offs:** Less impressive-sounding, but harder to hallucinate

### Decision 5: Equity ranker in MVP
- **Options:** (a) In ranking formula, (b) Metadata annotation only, (c) Removed
- **Recommendation:** Metadata annotation only
- **Trade-offs:** More honest, but less "socially-aware" positioning

---

## Answers to 25 Explicit Questions

### Scope Questions (1-3)

**Q1: Is RA truly the best first primary disease?**
**Yes.** Public data density, evaluation tractability, and mechanistic interpretability all favor RA over alternatives. No other autoimmune disease has comparable density of public ChEMBL targets, ClinicalTrials trials, and PubMed literature.

**Q2: If not RA, what single disease would replace it?**
**No replacement needed.** RA is the correct choice. If forced to choose an alternative: Type 2 diabetes (equal data density, different mechanistic class — metabolic vs. inflammatory). But RA is preferable because the adjacency set (SLE, PsA, Sjogren) provides richer cross-disease reasoning signals.

**Q3: Should adjacent autoimmune diseases be queryable in MVP?**
**No.** Adjacent diseases should appear only as graph context. Making them queryable in MVP would multiply the ontology resolution burden, evaluation surface area, and risk of shallow adjacency reasoning being mistaken for genuine cross-disease discovery.

### Input and Ontology Questions (4-6)

**Q4: Should MVP accept only enumerated diseases or free-text strings?**
**Accept both, but with strict bounds.** Accept (a) canonical UMLS CUI, (b) curated string aliases from a shortlist. Reject everything else with an error listing supported diseases.

**Q5: What ontology strategy for MVP?**
**UMLS CUIs.** Already partially implemented in the seed graph. Free, well-mapped to ChEMBL and PubMed data. No licensing restrictions. Can be upgraded to a richer ontology post-MVP.

**Q6: How to handle synonyms without sloppy mappings?**
**Curated synonym table, not automated expansion.** Manually create a 10-15 entry synonym list per disease. Accept known variants, reject ambiguous terms (e.g., "arthritis" → reject, "rheumatoid arthritis" → accept).

### Graph Questions (7-9)

**Q7: What is the minimum real-data subgraph for meaningful path explanations?**
**~500 nodes, ~2,000 edges.** Below this threshold, most drug-disease paths will collapse to Drug → Target → Disease, providing no path diversity. The current 18-node graph is ~25x too small.

**Q8: Which path types are essential for MVP?**
- P0: Drug → Target → Disease (core mechanism)
- P0: Drug → Trial → Disease (trial evidence)
- P1: Drug → Target → Pathway → Disease (mechanistic depth)
- P2: Other types (future)

**Q9: How should provenance and confidence be stored?**
Every edge must have: `source_db`, `confidence (0-1)`, `pmid` (where available), `evidence_year`, `source_record_id`. See full schema in `data/dripe_deliverable_B_graph_spec.md`.

### Ranking Questions (10-13)

**Q10: Should GAT lead the MVP ranking?**
**No.** The current GAT, trained on 12 edges, is plumbing test code. Lead with graph heuristics (path count). Use GAT as 15% auxiliary signal.

**Q11: What non-neural baselines are required?**
1. Common-neighbor path score
2. Weighted path count (confidence product)
3. Random baseline

**Q12: How to construct composite ranking before validation?**
`composite = 0.40 * path_score + 0.25 * evidence_score + 0.20 * trial_score + 0.15 * gnn_score`
Weights are heuristic — chosen to favor interpretable signals. Must be validated and potentially revised after first evaluation run.

**Q13: How to handle known-indication leakage?**
Two strategies: (1) During evaluation, exclude known RA indications from candidate pool. (2) Report recall@K separately for known vs. novel candidates.

### Retrieval Questions (14-16)

**Q14: What to index first — PubMed abstracts, trial summaries, or both?**
**Both.** PubMed abstracts for mechanism evidence, trial summaries for clinical evidence. Target: ~500 abstracts + ~200 trials for RA MVP (~1,700-2,700 chunks).

**Q15: How to generate retrieval queries from graph outputs?**
**Candidate-aware query construction.** Build queries from drug_name + disease_name + target_names_from_path + keywords ("mechanism", "pathway", "trial", "repurposing"). Generate 3 queries per candidate, deduplicate results.

**Q16: How to surface contradictory evidence?**
**Rule-based detector for MVP:**
- OpenFDA Grade 3+ adverse events → flag
- Literature mentioning "no significant benefit" or "failed endpoint" → flag
- Terminated trials → flag
Weak or missing evidence → add "sparse_support" counter-evidence entry

### Explanation Questions (17-19)

**Q17: Structured JSON only, or JSON + prose?**
**JSON + short plain language summary.** Three fields: `structured_summary` (1-3 sentences with specific entity references), `plain_language_summary` (1-2 sentences, no jargon), `uncertainty_statement` (explicit limitations). No free-form prose.

**Q18: Should `chain_of_thought.py` be kept, renamed, or redesigned?**
**Keep the filename, redesign the concept.** The prompt must be restructured to produce constrained JSON output anchored to supplied evidence. The current free-form generation approach is not suitable for MVP.

**Q19: How to test explanation groundedness?**
**Manual review protocol.** For top-5 outputs per query: (1) Verify cited paths exist in Neo4j, (2) Check cited PMIDs are real, (3) Compare LLM summary against source texts, (4) Flag any hallucinated entity or relationship. Automatable in future versions.

### Evaluation Questions (20-22)

**Q20: What is the most honest MVP evaluation using only public data?**
**Known-therapy recovery from FDA labels + ClinicalTrials + PubMed.** Construct a gold standard of ~65 known RA-associated drugs. Measure recall@K. Always report alongside path-count heuristic baseline and random baseline.

**Q21: What counts as success for v1?**
- Recall@10 ≥ 30% (beats random)
- 80%+ top-10 candidates have real graph paths
- 70%+ top-5 explanations are faithful to evidence
- 100% responses have uncertainty statements
- Zero clinical language violations

**Q22: What failure patterns are most likely in RA-scoped autoimmunity?**
1. **Graph sparsity** — not enough paths to rank meaningfully
2. **Hub-node bias** — TNF and JAK appear in every path
3. **Overly generic explanations** — "this drug targets inflammation"

### Product Boundary Questions (23-25)

**Q23: Which modules are worth keeping unchanged?**
- **Guardrails** (`query_classifier.py`) — works, keep
- **Disclaimer injector** — works, keep
- **GraphEngine** (`graph_builder.py`) — core infrastructure, keep
- **FAISS vectorstore** (`vectorstore.py`) — well-designed, keep
- **Embedder** (`embedder.py`) — correct model choice, keep
- **Retriever** (`retriever.py`) — conceptually correct, keep (improve query construction)

**Q24: Which modules need conceptual downgrading or redesign?**
- **GNN `inference.py`** — downgrade from primary to secondary signal
- **`chain_of_thought.py`** — redesign prompt from free-form generation to constrained structured output
- **Equity ranker** — demote from ranking component to metadata annotation

**Q25: Which pieces are engineering scaffolding, not scientific contribution?**
- FastAPI app (`api/main.py`) — standard CRUD scaffolding
- Ollama client (`client.py`) — off-the-shelf integration
- Data loaders (`data_loader.py`) — standard Neo4j → PyTorch bridge
- Rate limiter (`rate_limiter.py`) — not wired, infrastructure only
- Changelog generator, snapshot manager — operational tooling

---

## Deliverables Created

| File | Content |
|------|---------|
| `data/dripe_deliverable_A_disease_scope.md` | RA scope decision, ontology strategy, query input design |
| `data/dripe_deliverable_B_graph_spec.md` | Node/edge schema, path types, provenance, coverage report design |
| `data/dripe_deliverable_C_ranking_spec.md` | Composite scoring, baselines, GNN role, novelty buckets |
| `data/dripe_deliverable_D_retrieval_explanation_spec.md` | Indexing plan, candidate-aware queries, explanation JSON, contradiction handling |
| `data/dripe_deliverable_E_evaluation_spec.md` | Benchmark setup, metrics, manual review, error taxonomy, success criteria |
| `data/dripe_deliverable_F_risk_register.md` | Risk assessment, scientific weakness analysis, overclaim boundaries |
