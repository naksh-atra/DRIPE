# DRIPE Agent Handoff: MVP Re-Scope, Disease Program Strategy, and Immediate Execution Plan

## Purpose of This Handoff

This document is a reset and refinement directive for DRIPE.

The project already has a meaningful technical skeleton: guardrails, a Neo4j graph layer, a GAT-based scoring module, a retrieval stack, a local-LLM explanation layer, and API exposure. However, the live system is still operating on a toy seed graph and disconnected ingestion paths, which means the current implementation proves architecture wiring more than scientific validity.

The immediate goal is **not** to make DRIPE broader. The immediate goal is to convert DRIPE into a **disease-scoped, evaluation-heavy, explainability-first research platform** that a technically serious researcher could inspect, critique, and potentially adopt for hypothesis generation.

This handoff should be treated as the new working brief.

---

## 1. Project Reframing

### DRIPE is not trying to be:
- A general biomedical chatbot.
- A clinical decision support system.
- A patient-facing tool.
- A broad “all diseases” repurposing engine.
- A system whose credibility depends on LLM prose.

### DRIPE should now be defined as:

> A research-only, disease-program-specific drug repurposing workbench that ranks candidate drug–disease hypotheses from a structured knowledge graph, grounds them in retrieved evidence, and explains them through inspectable paths and constrained summaries.

### Core principle
The graph and evidence should do the reasoning. The LLM should do bounded synthesis.

That means:
- No free-form speculative mechanism narration.
- No outputs that appear clinically prescriptive.
- No ranking system that depends only on one model score.
- No claims of novelty without explicit labeling.

---

## 2. Why the Scope Must Change

The current codebase is architecturally interesting, but scientifically underpowered because:
- the production graph is a tiny seed graph;
- ingestion connectors are not yet feeding the live pipeline;
- explanation quality cannot yet be meaningfully judged on real evidence;
- the GNN is not yet being evaluated against defensible baselines on real disease-program data;
- disease input is still too open relative to current ontology and evidence handling.

The answer is not “add more components.”
The answer is “reduce scope, increase validity.”

The MVP should therefore optimize for:
1. bounded disease scope;
2. real public data integration;
3. explicit evidence objects;
4. reproducible ranking outputs;
5. built-in evaluation;
6. clear failure disclosure.

---

## 3. Recommended Disease Scope

### Recommendation
Use a **narrow rheumatic autoimmune disease program** for the first real MVP.

### Primary disease recommendation
**Rheumatoid arthritis (RA)** should be the primary MVP disease.

### Adjacency diseases for graph context
Use a small number of related diseases as contextual neighbors, not as equal first-class targets:
- systemic lupus erythematosus (SLE)
- psoriatic arthritis (PsA)
- Sjogren disease / Sjogren syndrome

### Why this scope is preferred
Rheumatoid arthritis is a better first disease than a broad autoimmune umbrella because it gives the system:
- a more teachable disease concept space;
- a clearer existing therapy landscape;
- more interpretable adjacent-disease reasoning;
- a better chance of evaluating whether the system recovers known and adjacent therapeutic patterns.

### Important scoping rule
The MVP should **not** support all autoimmune diseases.
It should support **one primary disease** and a **small adjacency set** used for graph context and cross-disease reasoning.

---

## 4. New MVP Definition

### One-line MVP definition
Given a supported disease (starting with rheumatoid arthritis), DRIPE should return a ranked shortlist of existing drugs along with graph-grounded evidence, retrieved literature/trial context, explicit uncertainty disclosures, and a constrained explanation of why the candidate may merit follow-up review.

### The MVP must answer exactly one question well
> For this disease, which existing drugs are worth reviewing next, and why?

### The MVP does **not** need to answer:
- whether the drug works clinically;
- whether a patient should receive it;
- whether the hypothesis is novel in the strict scientific sense;
- whether the system has discovered a therapeutic truth.

The MVP is a **hypothesis prioritization and evidence-packaging system**.

---

## 5. What the Current Architecture Should Become

The current architecture already has the right broad modules. The task is to tighten their role.

### 5.1 Guardrails
Keep the existing guardrails, but strengthen the intent classification boundary.

#### Desired behavior
- Allow only research-oriented disease-program queries.
- Reject patient-specific, diagnosis-seeking, or treatment-seeking requests.
- Reject clinician-style prescription requests.
- Inject research-only disclaimers consistently.

#### Today’s output expected
- A short note describing current classifier behavior.
- A list of current false-positive / false-negative patterns.
- A proposal for the exact allowed query schema for MVP.

#### Nuanced decision required
Should the MVP accept only canonical disease identifiers from a dropdown/API enum, or also accept disease strings that are then normalized?

**Agent must answer with a recommendation and rationale.**

---

### 5.2 Graph Layer
The graph layer should become the center of the product, not just a data store.

#### Current role
- Neo4j connectivity
- simple path traversal
- edge confidence
- coverage reporting

#### Required new role
The graph layer must:
- represent a real disease-program subgraph;
- preserve provenance for every ingested edge;
- support richer paths than only Drug → Protein → Disease;
- make coverage gaps visible;
- expose path evidence as a first-class output object.

#### Required path expansion
The graph should be able to surface candidate explanatory paths such as:
- Drug → Target → Disease
- Drug → Target → Pathway → Disease
- Drug → Target → Gene/Protein → Phenotype → Disease
- Drug → Adverse Event / Phenotypic signal → Disease-context relevance
- Drug → Trial evidence → Disease

Not all of these need to be live on day one, but the graph schema should allow them.

#### Today’s output expected
1. A proposed **MVP graph schema** with node types, edge types, and provenance fields.
2. A proposal for how disease-program filtering is implemented in Neo4j.
3. A design for a `supporting_paths` output object.
4. A design for a `coverage_report` object that clearly communicates missing evidence.

#### Nuanced decisions required
The agent must answer:
- What is the minimum viable subgraph for RA-focused MVP?
- Which node/edge types are mandatory now vs optional later?
- Should path traversal be schema-constrained by allowed metapaths, or open-ended with ranking afterward?

The response must include trade-offs.

---

### 5.3 GNN / Ranking Layer
The GNN should remain in the system, but it should stop being the sole prestige component.

#### New principle
A candidate should not appear strong only because a single learned model says so.

#### The ranking layer must combine:
- graph/topological score or heuristic score;
- learned link-prediction score (GNN or KG embedding-based score);
- evidence support score from retrieval/trials;
- novelty/status labeling.

#### Desired output shape per candidate
Each candidate should eventually include:
- `graph_score`
- `learned_score`
- `evidence_score`
- `composite_score`
- `novelty_bucket`
- `confidence_notes`

#### Baselines are mandatory
The agent should propose at least one simple baseline to compare against the GNN, for example:
- common-neighbor style graph heuristic;
- path-count / weighted path heuristic;
- simpler embedding model;
- known-link prior from graph neighborhoods.

#### Today’s output expected
1. A revised ranking architecture note.
2. A proposal for baseline models/heuristics.
3. A draft candidate-scoring schema.
4. A plan for distinguishing:
   - known indication,
   - adjacent/off-label signal,
   - trial-explored,
   - exploratory candidate.

#### Nuanced decisions required
The agent must answer:
- Should GAT stay the MVP model, or should a simpler, more interpretable baseline be preferred initially?
- How should the composite score be constructed before any large-scale validation exists?
- Is the current seed-graph-trained model useful for anything beyond software plumbing tests?

The answer should be blunt and technically honest.

---

### 5.4 Retrieval Layer
The retrieval layer is currently conceptually correct but operationally under-realized.

#### New rule
Retrieval should support the graph hypothesis; it should not become an unstructured search fallback.

#### Desired behavior
For each top candidate, retrieve a small evidence packet that may include:
- supporting PubMed abstract chunks;
- disease-specific mechanistic mentions;
- trial references or trial summaries;
- contradictory or weak-evidence signals if available.

#### Retrieval should be candidate-aware
Queries should not be generic disease-only lookups. They should be built from:
- disease name + synonyms;
- candidate drug name + synonyms;
- mechanistic anchor entities from the graph path;
- terms like mechanism / pathway / repurposing / trial / inflammatory.

#### Today’s output expected
1. A design for candidate-aware retrieval query construction.
2. A proposal for literature chunking and metadata fields.
3. A plan for linking retrieval output back to graph paths.
4. A proposal for what to do when literature is sparse or contradictory.

#### Nuanced decisions required
The agent must answer:
- Should retrieval index only abstracts in MVP, or abstracts + trial summaries?
- Should top-k retrieval be fixed or adaptive based on evidence density?
- How should contradictory evidence be surfaced rather than hidden?

---

### 5.5 LLM Layer
The LLM layer should be downgraded from “reasoning engine” to “constrained evidence narrator.”

#### Critical instruction
Do **not** let the model generate broad biological explanations untethered from graph and retrieval evidence.

#### New role
The LLM should take:
- candidate metadata,
- score breakdown,
- supporting paths,
- retrieved evidence,
- counter-evidence,
- coverage limitations,

and produce:
- a concise structured explanation;
- a plain-language rationale;
- explicit uncertainty statements;
- no treatment advice.

#### Explanation style requirements
- grounded in supplied artifacts only;
- concise and inspectable;
- able to say “evidence is weak / sparse / inconsistent”;
- explicitly non-clinical;
- never pretending novelty.

#### Today’s output expected
1. A revised prompt contract for the LLM.
2. A proposal for structured explanation JSON.
3. A list of forbidden behaviors and required disclaimers.
4. A recommendation on whether “chain_of_thought.py” should be renamed or redesigned conceptually.

#### Nuanced decisions required
The agent must answer:
- Should DRIPE expose full free-form explanations at all, or mainly structured summaries with short narrative text?
- How should the system communicate uncertainty without becoming uselessly cautious?
- How should safety filtering interact with evidence-grounded explanation generation?

---

### 5.6 Equity Ranker
This component is interesting, but it should not distort the MVP before biomedical validity is established.

#### Recommendation
Do not remove it, but demote it from core ranking logic for the first real MVP.

#### Preferred role for now
Use equity-related signals as an annotation or secondary view, not as a dominant ranking criterion.

#### Today’s output expected
- A recommendation note on whether the equity ranker should be:
  - disabled in composite ranking,
  - retained as metadata only,
  - or used as an optional post-ranking view.

The agent must explain the implications of each choice.

---

## 6. Exact MVP Output Contract

The current response object needs to become stricter and more inspectable.

### Proposed response structure per query

```json
{
  "query": {
    "disease_input": "rheumatoid arthritis",
    "canonical_disease_id": "...",
    "query_status": "accepted"
  },
  "program_scope": {
    "primary_disease": "rheumatoid arthritis",
    "adjacent_diseases_considered": ["systemic lupus erythematosus", "psoriatic arthritis", "sjogren disease"]
  },
  "coverage_report": {
    "graph_density_note": "...",
    "literature_density_note": "...",
    "trial_evidence_note": "...",
    "known_limitations": ["..."]
  },
  "candidates": [
    {
      "drug_name": "...",
      "ranking_scores": {
        "graph_score": 0.0,
        "learned_score": 0.0,
        "evidence_score": 0.0,
        "composite_score": 0.0
      },
      "novelty_bucket": "known_indication | adjacent_offlabel | trial_explored | exploratory",
      "supporting_paths": [
        {
          "path_type": "Drug-Target-Pathway-Disease",
          "nodes": ["..."],
          "edges": ["..."],
          "path_confidence": 0.0,
          "provenance": ["..."]
        }
      ],
      "retrieved_evidence": [
        {
          "source_type": "pubmed | trial",
          "identifier": "...",
          "title": "...",
          "snippet": "...",
          "relevance_score": 0.0
        }
      ],
      "counter_evidence": [
        {
          "type": "sparse_support | contradictory_signal | known_failure | missing_trial_context",
          "detail": "..."
        }
      ],
      "explanation": {
        "structured_summary": "...",
        "plain_language_summary": "...",
        "uncertainty_statement": "..."
      }
    }
  ],
  "research_only_disclaimer": "..."
}
```

### Today’s output expected
The agent should return:
1. a critique of this contract,
2. a refined final contract,
3. field-level notes on what is required for MVP vs later versions.

---

## 7. Evaluation is Part of the Product

This is a hard requirement.
If DRIPE cannot explain how it was evaluated, it is not ready as a credible research platform.

### Evaluation must be first-class
The agent should design evaluation for:
- ranking quality;
- known-therapy recovery;
- adjacent-disease recovery;
- explanation groundedness;
- evidence traceability;
- uncertainty honesty.

### Minimum MVP evaluation ideas
- Does the system recover drugs already associated with RA?
- Does it surface reasonable adjacent-disease signals before surfacing wild candidates?
- Are top explanations anchored to real paths and retrieved evidence?
- Does the system disclose sparse evidence rather than oversell?

### Today’s output expected
The agent should produce an **evaluation plan** containing:
1. candidate benchmark strategy;
2. baseline comparisons;
3. metrics to compute;
4. manual review protocol for top outputs;
5. error categories.

### Mandatory error taxonomy draft
At minimum, categorize failures such as:
- ontology mismatch;
- graph sparsity;
- hub-node bias;
- unsupported explanation;
- literature retrieval mismatch;
- trial evidence mismatch;
- already-known-but-presented-as-novel;
- overly generic immune-pathway explanation.

#### Nuanced decisions required
The agent must answer:
- What is the most defensible evaluation setup using only public data?
- How should “success” be defined for MVP without pretending prospective validation?
- How should known indications be handled in evaluation so the model is not rewarded for obvious memorization?

---

## 8. What Must Be Done Today

The objective for today is **design convergence**, not endless coding.
By end of today, the agent should provide a concrete written plan that freezes the MVP direction.

### Deliverable A — Disease Program Decision Memo
A markdown note that answers:
- Why RA is or is not the best first primary disease.
- Whether the adjacency diseases proposed are appropriate.
- What exact disease list the MVP should support.
- What disease ontology strategy will be used.

### Deliverable B — Data and Graph Spec
A markdown note that defines:
- minimum viable data sources for MVP;
- graph node and edge schema;
- provenance fields;
- disease-program filtering strategy;
- path types to support.

### Deliverable C — Ranking and Evidence Spec
A markdown note that defines:
- baseline scoring methods;
- GNN role in MVP;
- candidate score schema;
- novelty bucket definitions;
- evidence-score strategy.

### Deliverable D — Retrieval and Explanation Spec
A markdown note that defines:
- indexing plan;
- retrieval query construction;
- candidate evidence packet structure;
- explanation JSON schema;
- prompt constraints;
- contradiction handling.

### Deliverable E — Evaluation Spec
A markdown note that defines:
- benchmark setup;
- metrics;
- manual review criteria;
- error taxonomy;
- MVP success criteria.

### Deliverable F — Brutally Honest Risk Register
A markdown note listing:
- what will likely fail first;
- what is still scientifically weak;
- what is only software plumbing today;
- which modules should not be overclaimed externally.

---

## 9. Preferred Work Sequence for Today

The agent should work in this order:

1. **Decide disease scope**
   - Confirm or reject RA-centered autoimmune MVP.
   - If rejecting, propose exactly one better alternative and justify it.

2. **Define exact allowed input space**
   - Disease enum or disease normalization pipeline.
   - Allowed query forms.

3. **Freeze MVP graph schema**
   - Mandatory node types, mandatory edges, provenance model.

4. **Freeze ranking contract**
   - Baselines, GNN role, composite scoring philosophy.

5. **Freeze retrieval/explanation contract**
   - Evidence objects first, prose second.

6. **Freeze evaluation plan**
   - Metrics, review protocol, error buckets.

7. **List implementation tasks after design freeze**
   - Only after the above is settled.

---

## 10. Questions the Agent Must Explicitly Answer

These should not be skipped.
Each answer should include recommendation, rationale, and trade-offs.

### Scope questions
1. Is rheumatoid arthritis truly the best first primary disease for DRIPE, given current architecture and public-data constraints?
2. If not, what single disease should replace it, and why?
3. Should adjacent autoimmune diseases be used only for graph context, or also appear as alternate query targets in MVP?

### Input and ontology questions
4. Should MVP accept only enumerated diseases or also free-text disease strings?
5. What ontology or canonical-ID strategy should be used immediately?
6. How should synonym handling be implemented without introducing sloppy mappings?

### Graph questions
7. What is the minimum real-data subgraph needed to make path explanations meaningful?
8. Which path types are essential for MVP?
9. How should provenance and confidence be stored at the edge/path level?

### Ranking questions
10. Should GAT remain the central learned model for MVP, or should a simpler model/baseline lead initially?
11. What non-neural baselines must be included?
12. How should composite ranking be constructed before robust validation exists?
13. How should known-indication leakage be handled?

### Retrieval questions
14. What exactly should be indexed first: PubMed abstracts only, trial summaries only, or both?
15. How should retrieval queries be generated from graph outputs?
16. How should contradictory or weak literature be surfaced?

### Explanation questions
17. Should the system return structured explanation JSON only, or JSON plus short prose?
18. Should `chain_of_thought.py` be kept, renamed, or redesigned?
19. How should explanation groundedness be tested?

### Evaluation questions
20. What is the most honest MVP evaluation setup using only public data?
21. What counts as success for version 1?
22. What failure patterns are most likely in RA-scoped autoimmune repurposing?

### Product boundary questions
23. Which current modules are worth keeping unchanged?
24. Which current modules need conceptual downgrading or redesign?
25. Which pieces are present mainly as engineering scaffolding and should not be oversold?

---

## 11. Tone and Decision Standard

The agent should optimize for:
- scientific defensibility;
- inspectability;
- adoption by technical researchers;
- honest scoping;
- clarity over impressiveness.

The agent should **not** optimize for:
- sounding visionary;
- maximizing module count;
- pretending novelty;
- overclaiming what the current code proves.

When uncertain, the correct default is:
**narrow the scope, expose the uncertainty, and strengthen the evidence object.**

---

## 12. Final Instruction to the Agent

Treat this as a design reset with respect for the work already done.
The current architecture is valuable because it already embodies a graph-first, guarded, explainability-aware philosophy. The next step is to make that architecture scientifically coherent by constraining scope and making every output inspectable.

### What is needed back today
Return a structured response with these sections:
1. Recommended disease scope
2. MVP definition
3. Required changes by module
4. Proposed response contract
5. Evaluation framework
6. Risks and non-goals
7. Decisions requiring human approval

Wherever there is ambiguity or genuine trade-off, do **not** choose silently.
State the options, explain the trade-offs, and provide a recommendation.

