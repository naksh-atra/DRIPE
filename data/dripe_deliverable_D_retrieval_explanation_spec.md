# Deliverable D: Retrieval and Explanation Spec

## Status: Design Decision — 2026-03-22

---

## 1. Indexing Plan

### What to index for MVP

| Source | Material | Format | Priority |
|--------|----------|--------|----------|
| **PubMed abstracts** | Title + abstract for drug-disease pairs | Chunked text (200-word windows) | P0 — must have |
| **ClinicalTrials.gov** | Brief title + condition + outcomes | Full text (not chunked) | P0 — must have |

### Chunking strategy
- **PubMed:** Sliding window — 200 words, 20-word overlap
- **Trials:** Full trial summary as one "chunk" (trials are naturally concise)
- **Filtering:** Skip chunks containing only methods/statistics boilerplate

### Expected index size for MVP
| Source | Estimated Chunks |
|--------|-----------------|
| PubMed (RA-focused, 500 abstracts) | ~1,500-2,500 chunks |
| ClinicalTrials (RA-focused, 200 trials) | ~200 chunks |
| **Total** | ~1,700-2,700 |

### Metadata per chunk

```json
{
  "source_type": "pubmed | trial",
  "identifier": "PMID:34873336 | NCT01039559",
  "title": "...",
  "snippet": "...",
  "year": 2023,
  "drug_mentions": ["baricitinib", "methotrexate"],
  "disease_mentions": ["rheumatoid arthritis", "RA"]
}
```

---

## 2. Retrieval Query Construction

### Current approach (too generic)
```
query = f"drug {drug_name} mechanism disease {disease_name} repurposing therapeutic"
```

### MVP approach (candidate-aware)
For each drug-disease candidate, construct queries from the graph path:

```
query_string = f"{drug_name} {disease_name} {' '.join(target_names_from_path)} mechanism pathway trial"
```

Example for Baricitinib → JAK1 → RA:
```
query_string = "baricitinib rheumatoid arthritis JAK1 mechanism pathway trial"
```

### Multiple query strategy
Generate 3 queries per candidate, run all, deduplicate results:

| Query | Focus |
|-------|-------|
| Q1: `{drug} {disease} {targets} mechanism pathway` | Mechanism evidence |
| Q2: `{drug} {disease} trial` | Trial evidence |
| Q3: `{drug} {disease} repurposing repositioning` | Repurposing evidence |

### Deduplication
If the same PMID appears across queries, keep the highest relevance score.

---

## 3. Candidate Evidence Packet

```json
{
  "retrieved_evidence": [
    {
      "source_type": "pubmed",
      "identifier": "PMID:34873336",
      "title": "Baricitinib in rheumatoid arthritis: a systematic review",
      "snippet": "Baricitinib, a JAK1/JAK2 inhibitor, demonstrated efficacy in reducing RA disease activity...",
      "year": 2023,
      "relevance_score": 0.87
    },
    {
      "source_type": "trial",
      "identifier": "NCT01039559",
      "title": "A Study of Baricitinib in Patients With Rheumatoid Arthritis",
      "snippet": "Phase III, randomized, double-blind, placebo-controlled study...",
      "phase": "Phase 3",
      "status": "Completed",
      "relevance_score": 0.92
    }
  ],
  "counter_evidence": [
    {
      "type": "sparse_support",
      "detail": "Only 2 literature chunks found for this drug-disease pair. Evidence density is low."
    }
  ]
}
```

---

## 4. Explanation JSON Schema

```json
{
  "explanation": {
    "structured_summary": "Baricitinib is predicted to treat rheumatoid arthritis primarily through inhibition of JAK1 (P51681), a kinase involved in inflammatory cytokine signaling. This target-disease association is supported by known pharmacology (approved JAK inhibitor class) and clinical trial NCT01039559.",
    "plain_language_summary": "This drug works by blocking a protein called JAK1, which plays a role in inflammation. Blocking JAK1 reduces the inflammatory signals that cause rheumatoid arthritis symptoms.",
    "uncertainty_statement": "This hypothesis is supported by 4 graph paths, 3 literature references, and 1 completed Phase III trial. However, the current knowledge graph is small and retrieval coverage is limited. This should be treated as a prioritization signal, not clinical evidence.",
    "basis": {
      "graph_paths_count": 4,
      "literature_chunks": 3,
      "trial_count": 1,
      "evidence_tier": "MODERATE",
      "is_known_indication": true
    }
  }
}
```

### Field specification

| Field | Required | Content Rule |
|-------|----------|--------------|
| `structured_summary` | Yes | 1-3 sentences. Must reference specific entities (drug names, target names, trial IDs). |
| `plain_language_summary` | Yes | 1-2 sentences. No jargon. |
| `uncertainty_statement` | Yes | Must acknowledge: (1) graph limitations, (2) evidence density, (3) non-clinical nature. |
| `basis.graph_paths_count` | Yes | Integer count of supporting paths. |
| `basis.literature_chunks` | Yes | Integer count of retrieved literature chunks. |
| `basis.trial_count` | Yes | Integer count of associated trials. |
| `basis.evidence_tier` | Yes | One of: STRONG, MODERATE, WEAK, INSUFFICIENT |
| `basis.is_known_indication` | Yes | Boolean — is this drug already approved for this disease? |

---

## 5. Prompt Constraints

### Do not let the LLM write free-form speculative text

The `chain_of_thought.py` prompt must be restructured to produce structured output only:

```
SYSTEM: You are an evidence narrator. Do not write broad biological explanations.
Your task is to summarize supplied structured evidence into concise JSON.

You have been given:
- drug name: {name}
- disease name: {disease}
- graph paths: {paths}
- literature chunks: {literature}
- trial data: {trials}
- counter_evidence flags: {counter}

Produce a JSON object with:
1. structured_summary: 1-3 sentences referencing specific entities
2. plain_language_summary: 1-2 sentences without jargon
3. uncertainty_statement: explicit limitations

CONSTRAINTS:
- Do not add information not present in the supplied data
- Do not speculate about mechanisms not shown in the graph paths
- If evidence is sparse, say so directly
- Never use clinical language (prescribe, dose, treat clinically)
- If the drug is a known indication, say "known therapy for this disease"
```

---

## 6. Contradiction Handling

### What contradictions look like in MVP
- Drug has a graph path to RA but also a strong OpenFDA adverse event signal relevant to RA
- Literature supports mechanism X, another paper contradicts mechanism X
- Trial failed to meet primary endpoint but was still completed

### How to surface them
For MVP, implement a simple rule-based contradiction detector:
- If OpenFDA shows Grade 3+ adverse event for a candidate drug → add counter-evidence entry
- If literature mentions "no significant benefit" or "failed to meet endpoint" → flag
- If trial status is "Terminated" with negative reason → flag

### Counter-evidence in response
```json
{
  "counter_evidence": [
    {
      "type": "contradictory_signal",
      "detail": "This drug has a known adverse event (serious infection) that may limit applicability in RA patients."
    },
    {
      "type": "known_failure",
      "detail": "Trial NCT12345678 for this drug in RA was terminated due to lack of efficacy."
    }
  ]
}
```

---

## 7. `chain_of_thought.py` Recommendation

**Keep the file, redesign the concept:**

| Current | MVP |
|---------|-----|
| `PromptBuilder.build_cot_prompt()` | → Build constrained structured-output prompt |
| `generate_cot_explanation()` | → Generate JSON; strip speculative text |
| Returns free-form text | → Returns structured JSON |
| Untethered reasoning | → Evidence-anchored summarization |

The rename is unnecessary — `chain_of_thought` is fine as a directory name. What matters is the prompt contract change.
