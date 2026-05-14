# Deliverable C: Ranking and Evidence Spec

## Status: Design Decision — 2026-03-22

---

## 1. GAT Should Not Lead the MVP

**Blunt assessment:** The current GAT model, trained on 18 nodes and 12 edges, is useful only for proving the software pipeline works. It is not scientifically meaningful. Deploying it as the primary ranking signal would be intellectually dishonest.

### Recommendation for MVP ranking
**Lead with graph heuristics; use the GNN as a secondary signal.**

The GAT should be run and its scores reported, but the composite ranking for the MVP should be dominated by interpretable, inspectable signals:
1. Path count / weighted path confidence (graph heuristic)
2. Literature evidence support score (retrieval)
3. Trial evidence support score (from ClinicalTrials)
4. Learned score (GNN) — as an auxiliary signal only

---

## 2. Baseline Scoring Methods

### Baseline 1: Common-Neighbor Path Score
For each drug-disease pair (d, D):
- Count the number of distinct targets shared between d and D
- Weight by average target-disease association confidence
- Normalize by max count across all candidates

```
path_score(d, D) = Σ over targets t: confidence(t→D) / max_over_all_candidates
```

**Why this baseline:** Simple, interpretable, inspectable. If the GNN cannot beat this, the GNN is not adding value.

### Baseline 2: Weighted Path Count
For each drug-disease pair (d, D):
- Find all paths of length ≤ 3 from d to D
- Sum confidence product for each path
- Apply decay for longer paths (multiply by 0.7 per extra hop)

```
weighted_path_score(d, D) = Σ over paths p: product(edge confidences in p) * decay^(len(p)-1)
```

### Baseline 3: Random (lower bound)
Random permutation of candidates. No system should score below this.

---

## 3. Composite Score Construction

### Formula (MVP v1)

```
composite_score = 0.40 * normalized_path_score + 
                  0.25 * normalized_evidence_score + 
                  0.20 * normalized_trial_score + 
                  0.15 * normalized_gnn_score
```

### Why these weights
- **Path score (0.40):** The graph is the core evidence. This should dominate.
- **Evidence score (0.25):** Literature support grounds hypotheses in real data.
- **Trial score (0.20):** Trial evidence is strong signal — a drug in an RA trial is more credible than one without.
- **GNN score (0.15):** The GNN is a secondary signal until it's validated against baselines.

### Normalization
Each sub-score is min-max normalized across candidates for the current query.

### Handling missing data
If a candidate has no trial evidence, trial_score = 0. Do not impute.
If a candidate has no literature, evidence_score = 0.

---

## 4. Candidate Score Schema

```json
{
  "drug_name": "Baricitinib",
  "ranking_scores": {
    "graph_score": 0.78,
    "learned_score": 0.65,
    "evidence_score": 0.82,
    "trial_score": 0.90,
    "composite_score": 0.79
  },
  "score_components": {
    "path_count": 4,
    "avg_path_confidence": 0.78,
    "literature_chunks": 3,
    "trial_count": 12,
    "gnn_raw_score": 0.65,
    "normalization_note": "Scores min-max normalized across 15 candidates"
  }
}
```

---

## 5. Novelty Buckets

| Bucket | Definition | Example | Score Impact |
|--------|------------|---------|--------------|
| `known_indication` | Drug has FDA approval for RA | Methotrexate, Adalimumab, Baricitinib | Label only, no boost |
| `adjacent_offlabel` | Drug approved for an adjacent disease (PsA, SLE, JIA) | Ustekinumab (PsA → RA) | +0.10 composite |
| `trial_explored` | Drug has completed RA trial(s) but no RA approval | Sarilumab (prior to approval) | +0.05 composite |
| `exploratory` | Drug has graph path to RA but no trial or approval for RA | Any drug with target overlap only | No boost |

### Rationale
A drug already approved for RA should not be presented as a "discovery." It should be labeled clearly as a known therapy. The value of the system is in surfacing `adjacent_offlabel` and `trial_explored` candidates — drugs that are plausible but not officially repositioned.

---

## 6. Known-Indication Handling in Evaluation

### Problem
If the training set includes known RA drugs and the evaluation rewards the system for ranking them highly, the system is being rewarded for memorization, not prediction.

### Strategy
- During evaluation, exclude known RA indications from the candidate pool OR
- Measure recall@K separately for known vs. novel candidates
- Report both numbers

---

## 7. GNN Role in MVP

### Honest assessment
The GAT model should remain in the codebase because:
1. It proves the software pipeline works end-to-end
2. It can be retrained when the graph grows
3. It provides a learned signal that may become valuable at scale

### What it should NOT be used for in MVP
- Primary ranking signal
- Evidence for any claim about model quality
- Justification for any output

### Minimum graph size for meaningful GNN training
Based on GNN literature (You et al., 2020; Chami et al., 2022):
- Link prediction on graphs with < 1,000 edges rarely beats simple heuristics
- Meaningful GAT training likely requires 5,000+ edges with diverse path structures
- The current 12-edge graph is ~400x too small

**Target for meaningful GAT integration:** ≥ 5,000 edges from real ChEMBL/ClinicalTrials sources.
