# Deliverable E: Evaluation Spec

## Status: Design Decision — 2026-03-22

---

## 1. Evaluation Philosophy

DRIPE cannot validate hypotheses biologically. It can validate that its outputs are:
1. **Grounded** in real graph paths (not hallucinated)
2. **Ranked plausibly** relative to known therapy baselines
3. **Transparent** about evidence quality and limitations
4. **Reproducible** (same query → same output)

These four properties are what the evaluation should measure.

---

## 2. Benchmark Setup

### Gold standard construction
Create a known-therapy list for RA from public sources:

| Source | Content | Count (Target) |
|--------|---------|----------------|
| FDA drug labels (via DrugBank) | Approved RA therapies | ~20 |
| ClinicalTrials.gov Phase III completed | Drugs tested in RA but not approved | ~30 |
| PubMed systematic reviews | Off-label drugs mentioned in RA review articles | ~15 |
| **Total gold standard** | | **~65 known signals** |

### Seeding into the graph
These known therapies should be inserted into the graph as Drug→Disease edges with `source_db = "gold_standard"` and an `is_evaluation_only` flag.

### Two evaluation modes

**Mode A: Known-therapy recovery (standard evaluation)**
- Query the system for RA
- Count how many of the 65 known therapies appear in top-K
- Compare against baselines

**Mode B: Novelty-aware evaluation (harder evaluation)**
- Hide 30% of known therapies from the graph
- Check if GNN + path traversal predicts them anyway
- This measures whether the system recovers plausible candidates even when the "answer" edge is missing

---

## 3. Metrics

### Primary metrics

| Metric | Definition | Target for MVP |
|--------|------------|----------------|
| **Recall@10** | Fraction of gold-standard drugs in top 10 candidates | ≥ 30% |
| **Recall@20** | Same, top 20 candidates | ≥ 50% |
| **MRR** | Mean reciprocal rank of gold-standard drugs | ≥ 0.15 |
| **Novel candidate ratio** | Fraction of top-10 candidates not in gold standard | Reported (no threshold) |

### Secondary metrics

| Metric | Definition | Purpose |
|--------|------------|---------|
| **Explanation groundedness** | % of top-10 candidates where explanation cites at least one real graph path | Measures hallucination |
| **Uncertainty honesty** | % of top-10 candidates where uncertainty statement is non-empty and specific | Measures transparency |
| **Literature coverage** | % of top-10 candidates with ≥ 1 retrieved lit chunk | Measures retrieval quality |
| **Adjacent discovery rate** | % of top-10 candidates that are drugs for SLE/PsA/Sjogren but not RA | Measures adjacency value |

### Baseline comparisons
All primary metrics must be reported alongside:
1. Path-count heuristic baseline
2. Common-neighbor baseline
3. Random baseline

---

## 4. Manual Review Protocol (Qualitative)

For top-5 outputs in each evaluation run:

| Criterion | Question | Rating |
|-----------|----------|--------|
| Graph grounding | Is the top supporting path real and relevant? | Yes / Partial / No |
| Literature match | Does the retrieved literature actually discuss the claimed mechanism? | Yes / Partial / No |
| Explanation accuracy | Is the LLM explanation faithful to the supplied evidence? | Yes / Partial / No |
| Uncertainty | Is the uncertainty statement appropriate for the evidence quality? | Yes / Understates / Overstates |
| Clinical safety | Does the explanation avoid clinical language? | Pass / Fail |

### Manual review protocol
1. Run evaluation → get top-5 candidates per query
2. For each, independently verify path existence in Neo4j
3. Check if cited PMIDs actually exist
4. Compare LLM summary against source texts
5. Flag any hallucinated entity or relationship

---

## 5. Error Taxonomy

| Error Category | Definition | Likelihood (MVP) |
|----------------|------------|-------------------|
| **Ontology mismatch** | Disease query doesn't match canonical ID | Low (with enum-based input) |
| **Graph sparsity** | Too few paths to rank meaningfully | High (18 nodes) |
| **Hub-node bias** | Well-studied proteins dominate all paths | Medium |
| **Unsupported explanation** | LLM adds content not in supplied evidence | Medium |
| **Literature retrieval mismatch** | Retrieved chunk is semantically irrelevant | Medium |
| **Trial evidence mismatch** | Trial endpoint or condition doesn't match the drug-disease use case | Medium |
| **Known-indication presented as novel** | Drug is already approved but not labeled as such | Low (if novelty bucket works) |
| **Overly generic explanation** | "This drug targets inflammation" — no specific mechanism | High |
| **Missing counter-evidence** | Drug has known negative trial but doesn't appear in counter_evidence | Medium |

---

## 6. MVP Success Criteria

### Minimum bar for "this system is worth showing"
1. Recall@10 ≥ 30% (beats random baseline)
2. ≥ 80% of top-10 candidates have at least one real graph path
3. ≥ 70% of top-5 LLM explanations are faithful to supplied evidence
4. 100% of responses include non-empty uncertainty statements
5. System does not produce clinical language (automated check)

### Stretch goals
1. GNN-based score outperforms path-count heuristic (not expected at MVP scale)
2. Adjacent discovery rate ≥ 10%
3. Manual review shows ≤ 1 hallucinated entity per 5 explanations

---

## 7. Evaluation Automation

```python
# MVP eval script structure:
class MVP_Evaluator:
    def __init__(self, gold_standard_path, graph_engine, predictor, retriever):
        self.gold_standard = load_gold_standard(gold_standard_path)
    
    def evaluate_ranking(self):
        # Query RA
        # Score all candidates
        # Compute recall@K, MRR
        # Compare against baselines
    
    def evaluate_explanations(self):
        # For top-5: check path grounding, literature match, faithfulness
        # Return structured report
    
    def evaluate_uncertainty_honesty(self):
        # Check every response has non-empty uncertainty statement
        # Check statement is specific (not generic boilerplate)
    
    def run_full_evaluation(self):
        ranking_results = self.evaluate_ranking()
        explanation_results = self.evaluate_explanations()
        uncertainty_results = self.evaluate_uncertainty_honesty()
        return EvaluationReport(...)
```

## 8. Evaluation Report Format

```json
{
  "evaluation_date": "2026-03-22",
  "mvp_version": "v0.1",
  "graph_stats": {"nodes": 18, "edges": 12, "ra_specific_nodes": 6},
  "ranking_results": {
    "recall_at_10": {"value": 0.35, "baseline_path_count": 0.30, "baseline_random": 0.05},
    "recall_at_20": {"value": 0.55, "baseline_path_count": 0.50, "baseline_random": 0.10},
    "mrr": {"value": 0.18, "baseline_path_count": 0.15, "baseline_random": 0.02}
  },
  "explanation_results": {
    "groundedness_manual": {"pass": 4, "partial": 1, "fail": 0},
    "unsupported_claims": 0,
    "clinical_language_violations": 0
  },
  "uncertainty_results": {
    "non_empty_rate": 1.0,
    "specific_rate": 0.8,
    "boilerplate_rate": 0.2
  },
  "known_issues": [
    "Graph too small for meaningful GNN evaluation",
    "FAISS index contains only 16 chunks — retrieval evaluation is preliminary",
    "No manual review inter-rater reliability computed"
  ]
}
```
