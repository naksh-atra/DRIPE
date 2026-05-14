# DRIPE Project Goals

## Current Focus (2026-03-22)

### Primary Objectives
- [ ] Complete data ingestion pipeline (Neo4j seeding)
- [ ] Integrate GNN link prediction with API
- [ ] Wire RAG retrieval to LLM chain-of-thought

### Secondary Objectives
- [ ] Populate FAISS vector store with literature
- [ ] Implement equity ranker weighting
- [ ] Add real safety filter integration

### Nice to Have
- [ ] Transfer learning for rare diseases
- [ ] Equity dashboard in frontend
- [ ] Performance benchmarks

---

## Architecture Goals
- FastAPI backend with guardrails
- Neo4j knowledge graph (~10M nodes, 100M edges)
- Streamlit frontend with hypothesis explorer

## Data Sources (Planned)
- RTX-KG2 (foundation KG)
- ChEMBL (bioactivity)
- PubMed OA (literature)
- OpenFDA (adverse events)
- ClinicalTrials.gov (trial outcomes)

---

*Update this file weekly with progress and priorities.*
