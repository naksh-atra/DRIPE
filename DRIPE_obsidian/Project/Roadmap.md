# DRIPE Build Roadmap

## Phase 1: Infrastructure & Data Foundation ✓ COMPLETE
**Goal:** Get a working graph with real data

| Step | Task | Status |
|------|------|--------|
| 1.1 | Set up Docker + verify Neo4j connects | ✓ |
| 1.2 | Create seed script with sample KG data | ✓ |
| 1.3 | Complete ChEMBL connector | ✓ |
| 1.4 | Complete PubMed OA scraper | ✓ |
| 1.5 | Complete OpenFDA connector | ✓ |
| 1.6 | Complete ClinicalTrials connector | ✓ |

## Phase 2: ML Pipeline Integration ✓ COMPLETE
**Goal:** Wire GNN predictions into API

| Step | Task | Status |
|------|------|--------|
| 2.1 | Load graph data into PyTorch Geometric | ✓ |
| 2.2 | Train GAT model on sample subgraph | ✓ |
| 2.3 | Connect GNN output → API pipeline | ✓ |
| 2.4 | Implement link prediction scoring | ✓ |

## Phase 3: LLM + RAG Integration
**Goal:** Add reasoning layer

| Step | Task | Dependencies | Effort |
|------|------|-------------|--------|
| 3.1 | Set up FAISS vector store | Phase 1 | 1-2 hrs |
| 3.2 | Generate MedGemma embeddings | 3.1 | 2-3 hrs |
| 3.3 | Integrate RAG retriever with query | 3.2 | 2 hrs |
| 3.4 | Connect Anthropic API (real calls) | 2.3, 3.3 | 2 hrs |
| 3.5 | Wire chain-of-thought → API response | 3.4 | 1-2 hrs |

## Phase 4: Safety & Equity
**Goal:** Add guardrails and prioritization

| Step | Task | Dependencies | Effort |
|------|------|-------------|--------|
| 4.1 | Integrate safety filter (OpenFDA) | Phase 1 | 1 hr |
| 4.2 | Implement equity ranker (GBD) | None | 2 hrs |
| 4.3 | Add safety flags to responses | 4.1 | 1 hr |

## Phase 5: Frontend Polish
**Goal:** Improve UX

| Step | Task | Dependencies | Effort |
|------|------|-------------|--------|
| 5.1 | Add path visualization | Phase 2 | 2-3 hrs |
| 5.2 | Equity dashboard | 4.2 | 2 hrs |
| 5.3 | Hypothesis explorer improvements | Phase 3 | 2 hrs |

## Phase 6: Testing & Evaluation
**Goal:** Validate system

| Step | Task | Dependencies | Effort |
|------|------|-------------|--------|
| 6.1 | Integration tests | Phase 3 | 2 hrs |
| 6.2 | Run benchmarks | Phase 5 | 2 hrs |
| 6.3 | User testing | 6.1 | 1 hr |

---

**Total estimated time:** 40-60 hours

**Quick Start:** 1.1 → 1.2 (Docker + seed graph)
