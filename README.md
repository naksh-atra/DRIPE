# DRIPE: Drug Repurposing Intelligence Engine

DRIPE is an open-source research pipeline for drug repurposing, combining Knowledge Graphs, Graph Neural Networks (GNN), and LLM-based Chain-of-Thought reasoning.

## 🚨 Research Use Only
This system is provided for research purposes **ONLY**. It is not a clinical decision tool and must not be used to inform medical treatment.

## Architecture
- **Ingestion**: Pulls from RTX-KG2, ChEMBL, PubMed OA, OpenFDA, and ClinicalTrials.gov.
- **Graph Engine**: Neo4j-backed knowledge graph with confidence re-weighting.
- **Reasoning**: Link prediction via GAT (Graph Attention Network) and narration via MedGemma CoT.
- **Equity**: Integrated WHO GBD disease burden re-weighting.

## Quick Start
1. **Clone and Setup Environment**:
   ```bash
   cp .env.example .env
   # Update keys in .env
   ```
2. **Launch with Docker**:
   ```bash
   docker-compose up --build
   ```
3. **Access Interfaces**:
   - API: http://localhost:8000/docs
   - Frontend: http://localhost:8501

## License
Apache 2.0. Compatible with open-source biomedical data redistributions.
