# Drug Repurposing: Domain Knowledge

## What is Drug Repurposing?

Finding new therapeutic uses for existing, approved drugs.

**Advantages:**
- Reduced development time (3-5 years vs 10-15)
- Lower costs (up to 40% reduction)
- Established safety profiles

**Examples:**
- Sildenafil: angina → erectile dysfunction
- Thalidomide: sedation → leprosy/myeloma
- Minoxidil: blood pressure → hair loss

## Knowledge Graphs for Drug Repurposing

### Graph Structure
```
G = (V, E)
- Nodes (V): drugs, diseases, genes, pathways, anatomies
- Edges (E): treats, inhibits, causes, associated_with
```

### Key Relations
- `DRUGBANK.treats` - approved drug indications
- `Hetionet.CpD` - compound treats disease
- `GOBP.involved_in` - gene involvement in processes

## Graph Neural Networks (GNNs)

### Message Passing
Node embeddings aggregate neighbor features, capturing multi-hop dependencies:
```
drug → target → pathway → disease
```

### Graph Attention Networks (GAT)
Attention mechanisms weight paths by relevance, enabling transfer learning from high-resource to rare diseases.

## Retrieval-Augmented Generation (RAG)

Mitigates LLM hallucination by grounding reasoning in:
- KG subgraphs
- Literature (PubMed)
- Clinical data

## Equity Considerations

Post-prediction scoring:
```
S = P(link) × E(drug, disease)
```
Where E weights:
- GBD DALYs (disease burden)
- Affordability (generic status)
- Accessibility (supply chain)

## Links

- [[Architecture/System-Overview.md|System Architecture]]
- [[../aim.txt|Full Project Aim]]
