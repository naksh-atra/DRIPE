# DRIPE: Drug Repurposing Intelligence Engine

DRIPE is a research-only pipeline for drug repurposing hypothesis generation, focused on rheumatoid arthritis. It combines a biomedical knowledge graph, graph neural networks, RAG-based literature retrieval, and structured LLM explanations.

## Status — v2 Milestone

The architecture is proven and operational. The pipeline builds a reproducible RA-centered graph (602 nodes, 770+ edges), ranks drug candidates with interpretable scoring, retrieves supporting literature, and generates constrained explanations via a local/API LLM. **Current recall against known RA therapies is 0.0** because the graph currently contains ChEMBL assay compounds rather than approved drugs — the next variable is graph composition, not pipeline validity.

## Architecture

```
User Query (disease)
    │
    ▼
1. Disease Resolver  ── canonical ID lookup (RA only)
2. Path Traversal    ── Drug → Target → Disease paths in Neo4j
3. Composite Ranking ── graph score (40%) + evidence (25%) + trial (20%) + GNN (15%)
4. RAG Retrieval     ── FAISS semantic search over PubMed abstracts
5. LLM Narrator      ── structured JSON explanation (OpenRouter / local)
6. Evaluation        ── system vs path-count vs common-neighbor vs random
```

## Quick Start

### Prerequisites
- Python 3.10+
- Neo4j database (Aura cloud free tier recommended, or local Docker)
- OpenRouter API key for LLM explanations (free tier available)

### Setup
```bash
git clone https://github.com/naksh-atra/DRIPE.git
cd DRIPE
python -m venv dripenv
source dripenv/bin/activate    # Linux/Mac
dripenv\Scripts\activate       # Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Neo4j URI and OpenRouter key
```

### Build the RA graph
```bash
python -m scripts.build_ra_program_graph
```

### Start the API
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Test a query
```bash
python -m scripts.integration_test
```

### Run evaluation
```bash
python scripts/run_mvp_evaluation.py
```

## Key Modules

| Module | Purpose |
|--------|---------|
| `api/` | FastAPI endpoint with v2 response contract |
| `graph/` | Neo4j graph engine, path traversal, coverage reporting |
| `ranking/` | Composite scorer, novelty buckets, 3 baselines |
| `rag/` | FAISS index, candidate-aware retrieval, evidence packets |
| `llm/` | OpenRouter client, structured explanation prompts |
| `evaluation/` | Gold standard builder, ranking metrics, error taxonomy |
| `ingestion/` | RA-specific loaders for ChEMBL, ClinicalTrials.gov, PubMed |
| `config/` | Disease program definition (YAML) |

## License

Apache 2.0
