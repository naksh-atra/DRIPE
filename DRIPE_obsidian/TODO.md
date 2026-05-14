# DRIPE Task List

## In Progress

### Phase 4: Data Population
- [ ] Populate FAISS index with PubMed abstracts
- [ ] Fix Ollama issues (llama runner terminated)
- [ ] Test full pipeline with real data

### Safety & Equity
- [ ] Integrate safety filter (OpenFDA)
- [ ] Implement equity ranker (GBD)

## Blocked

- [ ] Ollama llama runner process terminated (500 error) - needs investigation

## Completed

- [x] Project scaffolding (folders, requirements)
- [x] FastAPI with guardrails
- [x] Streamlit frontend with dark theme
- [x] GAT model architecture defined
- [x] Chain-of-thought prompt builder
- [x] OpenCode + Obsidian second brain setup (2026-03-22)
- [x] Obsidian vault structure: Introduction, Goals, Domain-Knowledge, System-Overview
- [x] OpenCode model validation workaround (remove agent.build.model)
- [x] Neo4j local Docker setup with custom password (2026-03-22)
- [x] Seed graph script with 18 nodes, 12 edges (2026-03-22)
- [x] ChEMBL connector tested and working
- [x] PubMed OA scraper tested (PMIDs found, text simulated)
- [x] OpenFDA connector tested (adverse events retrieved)
- [x] ClinicalTrials.gov connector tested (trials retrieved)
- [x] PyTorch Geometric data loader (2026-03-22)
- [x] GAT model trained on sample graph (50% accuracy expected)
- [x] GNN inference module integrated with API (2026-03-22)
- [x] Link prediction scoring via GNN (2026-03-22)
- [x] Ollama LLM client (llama3.2) (2026-03-22)
- [x] Chain-of-thought explanation generation (2026-03-22)
- [x] FAISS vector store with SQLite metadata (2026-03-22)
- [x] Sentence transformer embedder (all-MiniLM-L6-v2) (2026-03-22)
- [x] RAG retriever integrated with API (2026-03-22)
- [x] Full GNN → RAG → LLM pipeline working (2026-03-22)

## Notes

- Update weekly
- Link completed tasks to relevant Obsidian notes
- Archive old completed tasks monthly

---

*Generated: 2026-03-22*
