# DRIPE System Architecture

## High-Level Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Ingestion │────▶│ Knowledge   │────▶│    GNN      │
│  (5 sources)│     │   Graph     │     │ Link Pred.  │
└─────────────┘     │   (Neo4j)   │     └──────┬──────┘
                    └─────────────┘            │
                         │                     ▼
                         ▼              ┌─────────────┐
                    ┌─────────────┐     │    RAG      │
                    │   Guardrails│◀────│ (Literature)│
                    │ (Query Class)     └─────────────┘
                    └─────────────┘            │
                         │                     ▼
                         ▼              ┌─────────────┐
                    ┌─────────────┐     │    LLM      │
                    │    API      │◀────│ Chain-of-   │
                    │  (FastAPI)  │     │   Thought   │
                    └─────────────┘     └─────────────┘
                         │
                         ▼
                    ┌─────────────┐
                    │  Frontend   │
                    │ (Streamlit) │
                    └─────────────┘
```

## Module Map

| Module | Path | Purpose |
|--------|------|---------|
| **API** | [[../api/main.py]] | FastAPI endpoints, orchestration |
| **Graph** | [[../graph/]] | Neo4j interactions, path traversal |
| **GNN** | [[../gnn/model.py]] | PyTorch Geometric GAT model |
| **LLM** | [[../llm/chain_of_thought.py]] | Chain-of-thought prompt builder |
| **RAG** | [[../rag/]] | Vector store and retrieval |
| **Guardrails** | [[../guardrails/query_classifier.py]] | Query classification, safety |
| **Frontend** | [[../frontend/app.py]] | Streamlit UI |

## Data Stores

| Store | Technology | Purpose |
|-------|------------|---------|
| Knowledge Graph | Neo4j Aura | ~10M nodes, 100M edges |
| Documents | MongoDB Atlas | Metadata, papers |
| Cache | Redis | Session data |
| Vectors | FAISS | Semantic search |

## API Endpoints

- `POST /query` - Main hypothesis generation
- `GET /health` - Service status

## Guardrails

1. **Query Classification** - Blocks patient-specific queries
2. **Disclaimer Injection** - Research-only warnings
3. **Safety Flags** - OpenFDA adverse event checking

## Links

- [[../Project/Goals.md|Project Goals]]
- [[../aim.txt|Full Technical Specification]]
