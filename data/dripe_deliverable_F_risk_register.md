# Deliverable F: Brutally Honest Risk Register

## Status: Risk Assessment — 2026-03-22

---

## 1. What Will Likely Fail First

| Risk | Likelihood | Impact | When It Manifests |
|------|------------|--------|-------------------|
| **GNN scores are random** on small graph | Very High | Medium | First real evaluation run |
| **Ollama crashes** under repeated queries | High | Medium | After 3-5 sequential API calls |
| **FAISS returns irrelevant chunks** with only 16 vectors | Very High | Medium | First retrieval evaluation |
| **Path traversal finds trivial paths** (all paths are Drug→Target→Disease, no diversity) | High | Medium | First RA query with real data |
| **Disease ontology resolution fails** (CUI not found or maps to wrong entity) | Medium | High | First non-RA query |
| **Edge confidence normalization is off** (all paths have similar confidence) | Medium | Low | Graph quality review |
| **Novelty bucket misclassifies drug** | Medium | Medium | When known drugs appear as "exploratory" |
| **Evaluation baseline beats GNN** | Very High | Low | Intended outcome (proves GNN is not ready) |

---

## 2. What Is Still Scientifically Weak

| Area | Current State | Why It's Weak | Path to Improvement |
|------|---------------|---------------|---------------------|
| **Knowledge graph** | 18 nodes, 12 edges | Smaller than a single student's literature review | Populate with real ChEMBL/ClinicalTrials data |
| **GNN model** | Trained on seed graph only | Cannot learn meaningful representations from 12 edges | Re-train on ≥ 5,000-edge graph |
| **GNN evaluation** | Not compared against baselines | Untested claim of "link prediction works" | Implement baseline comparison (this spec) |
| **LLM explanations** | Evaluated manually for one query | No systematic evaluation of faithfulness | Implement explanation groundedness eval (this spec) |
| **RAG retrieval** | FAISS has 16 chunks from 5 drug-disease pairs | Not representative of any real use case | Populate with 1,000+ PubMed abstracts |
| **Safety filter** | Keyword matching only | High false-positive / false-negative rate | Upgrade to classifier (post-MVP) |
| **Equity ranker** | Formula exists but not wired | Unvalidated weighting scheme | Post-MVP after biomedical validity is established |

---

## 3. What Is Only Software Plumbing Today

| Module | Current Role | Scientific Value (1-10) | Notes |
|--------|-------------|-------------------------|-------|
| **FastAPI app** (`api/main.py`) | HTTP request handling | 1 | Works. Standard CRUD scaffolding. |
| **Guardrails** (`query_classifier.py`) | Keyword-based intent classification | 2 | Blocks obvious misuse. Not a scientific contribution. |
| **Disclaimer injector** | Adds standard text | 1 | Legal/ethical requirement. Not research. |
| **GraphEngine** (`graph_builder.py`) | Neo4j driver wrapper | 3 | Necessary infrastructure. Not original. |
| **Data loaders** (`data_loader.py`) | Neo4j → PyTorch format | 4 | Necessary bridge. Pattern is standard. |
| **Ollama client** (`client.py`) | HTTP wrapper | 2 | Off-the-shelf integration. |

**These modules should not appear in any external description of DRIPE's scientific capabilities.** They are engineering infrastructure, not research contributions.

---

## 4. What Has Real (Even If Embryonic) Scientific Value

| Module | Current Role | Scientific Value | Why |
|--------|-------------|------------------|-----|
| **Path traversal** + edge confidence scoring | Graph-based hypothesis generation | 6 | Core intellectual contribution. Few drug repurposing systems expose inspectable paths. |
| **GNN + link prediction** | Learned scoring | 5 (potential: 8) | Scientifically appropriate approach. Not yet realized due to graph size. |
| **RAG retrieval** | Evidence grounding | 6 | Semantically correct approach. Retrieval quality will improve with index size. |
| **LLM chain-of-thought** | Explanation generation | 5 (potential: 7) | If constrained properly, a genuine contribution to explainability in drug repurposing. |
| **Evaluation framework** | Measurement | 7 (once implemented) | Most drug repurposing tools lack systematic evaluation. This is a differentiator. |

---

## 5. Which Modules Should Not Be Overclaimed Externally

### Do not claim:
- "We built a GNN that predicts drug repurposing opportunities" → The GNN has not been validated
- "Our system discovers novel therapies" → It recovers known patterns from a tiny graph
- "LLM generates biologically grounded explanations" → Groundedness has not been systematically evaluated
- "We covered all autoimmune diseases" → Only RA is supported
- "Equity-weighted ranking ensures fair outcomes" → Equity ranker is not validated

### Honest external description:
> "DRIPE is a research platform that ranks drug repurposing hypotheses for rheumatoid arthritis by combining knowledge graph paths, literature retrieval, and a graph neural network, with an emphasis on inspectable outputs and uncertainty disclosure."

---

## 6. Key Numbers to Communicate

| Number | What It Represents | Honest Context |
|--------|-------------------|----------------|
| 18 | Current graph nodes | A single human expert knows more about RA |
| 12 | Current graph edges | Equivalent to reading 3-4 papers |
| 16 | FAISS literature chunks | ~4 abstracts from PubMed |
| 0.005-0.03 | GNN score range | Not interpretable at this scale |
| ~55s | Query response time | Acceptable for dev; too slow for interactive use |
| 1 | Number of primary diseases supported | RA only |

---

## 7. What to Say in an Interview

> *"I built a drug repurposing pipeline that takes a disease name, finds graph paths to known drugs, scores them with link prediction, retrieves supporting literature, and generates structured explanations — with evaluation against baselines built in."*

**Defensible because:**
- The pipeline exists and works end-to-end (demonstrated)
- Evaluation against baselines is specified (if implemented)
- Structure is honest about the small graph (if communicated)
- Focus is on inspectability, not discovery claims (true to current design)

**Not defensible:**
- Claiming the GNN "works" for drug repurposing
- Claiming any discovery or validation
- Claiming clinical relevance
