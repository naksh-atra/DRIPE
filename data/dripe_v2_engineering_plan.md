# DRIPE v2 Engineering Plan

## Status

Implementation plan for immediate execution after design freeze.

This document translates the MVP design decisions into an engineering workflow that can be acted on immediately. It assumes the following are already accepted unless explicitly revised:

* Primary disease scope: rheumatoid arthritis (RA)
* Adjacency diseases for graph context only: SLE, PsA, Sjogren
* Research-only product boundary
* Graph-first, evidence-grounded, explainability-first pipeline
* GNN retained as auxiliary signal, not lead ranker
* Evaluation treated as a first-class product component

\---

## 1\. Objective

Build the first scientifically defensible version of DRIPE as a **disease-scoped drug repurposing research workbench** for rheumatoid arthritis.

The goal of v2 is not broad disease coverage, clinical relevance, or novelty claims. The goal is to produce an end-to-end system that:

1. accepts a supported disease query;
2. resolves it safely to a canonical disease ID;
3. constructs a real RA-centered biomedical subgraph;
4. ranks drug candidates using inspectable graph and evidence signals;
5. retrieves supporting literature and trial context;
6. returns structured explanations with explicit uncertainty;
7. evaluates its own ranking and explanation quality against public-data baselines.

\---

## 2\. Product Boundary

### v2 is

* A research-only API-first system
* A single-disease-program workbench
* A public-data hypothesis prioritization engine
* A graph + retrieval + constrained explanation system
* A benchmarkable and inspectable prototype

### v2 is not

* A patient-facing product
* A clinician decision-support system
* A general biomedical assistant
* An all-autoimmune exploration platform
* A validated discovery engine

\---

## 3\. Success Criteria

DRIPE v2 is considered implemented when the following are all true:

### Functional success

* RA query is accepted through a bounded input contract.
* System runs end-to-end on real ingested data, not seed graph alone.
* At least one RA query returns a ranked candidate list with graph paths, retrieval evidence, counter-evidence, and structured explanation.
* API returns stable JSON shaped by the agreed contract.

### Data success

* Real RA-relevant subgraph exists in Neo4j.
* FAISS index contains meaningful literature/trial content.
* Candidate ranking includes graph score, evidence score, trial score, and auxiliary learned score.

### Evaluation success

* Ranking is compared against at least three baselines.
* Known-therapy recovery metrics are computed.
* Explanation groundedness review can be run.
* Uncertainty statements are present and non-boilerplate.

### Scientific honesty success

* Known RA therapies are labeled as known indications.
* Unsupported candidates are not oversold.
* The GNN is not described as a validated discovery model.
* Coverage limitations are surfaced in responses.

\---

## 4\. Workstreams

Implementation should proceed in six workstreams. These workstreams are logically ordered, but some tasks can overlap.

1. Input and scope hardening
2. Data ingestion and graph build
3. Ranking engine redesign
4. Retrieval and explanation redesign
5. Evaluation system implementation
6. API integration and final response assembly

\---

## 5\. Immediate Execution Order

This is the recommended order of execution.

### Phase 0 — Freeze interfaces before coding

Implement nothing substantial until the following are frozen in code or config:

* supported disease list
* canonical disease IDs
* graph schema
* response contract
* score field names
* novelty bucket names
* explanation JSON fields
* evaluation metric names

### Phase 1 — Replace toy substrate

Priority is to stop relying on the seed graph as the meaningful production substrate.

### Phase 2 — Make outputs inspectable

Every candidate must expose graph paths, evidence, and limitations.

### Phase 3 — Add evaluation hooks

Evaluation should not be bolted on after the system appears to work.

### Phase 4 — Reintroduce learned components carefully

Only after baselines and real graph evidence are working should the GNN be reintroduced into ranking as an auxiliary signal.

\---

## 6\. Module-by-Module Engineering Plan

## 6.1 Guardrails and Input Layer

### Goal

Constrain the system to research-only RA-program queries and eliminate free-form disease ambiguity.

### Current modules

* `guardrails/query\_classifier.py`
* `guardrails/disclaimer\_injector.py`

### Required changes

#### A. Replace free disease input with bounded disease contract

Implement a disease config file, e.g.:

* `config/disease\_program.yaml`

It should define:

* `primary\_disease`
* `primary\_cui`
* `allowed\_aliases`
* `adjacency\_diseases`
* `adjacency\_cuis`
* `rejected\_aliases`

Example fields:

* rheumatoid arthritis
* RA
* C0003873
* lupus / SLE / C0024141 as graph-context only

#### B. Add query schema validation

Introduce a query object such as:

* `disease\_input`
* `canonical\_disease\_id`
* `query\_mode`
* `accepted`
* `rejection\_reason`

#### C. Tighten classifier behavior

The classifier should distinguish:

* accepted: disease-program research query
* rejected: patient-specific request
* rejected: diagnosis-seeking request
* rejected: treatment/prescription request
* rejected: unsupported disease

#### D. Make allowed disease input explicit in API docs

If a disease is unsupported, return a clear error listing supported diseases.

### New files or refactors

* `config/disease\_program.yaml`
* `schemas/query.py`
* `services/disease\_resolver.py`
* update `query\_classifier.py`

### Definition of done

* API accepts only supported disease IDs / aliases.
* Query normalization is deterministic.
* Unsupported or ambiguous disease strings are rejected with clear errors.
* Research-only disclaimer is always included in accepted responses.

\---

## 6.2 Data Ingestion and Graph Build

### Goal

Build a real RA-centered subgraph that replaces the seed graph as the meaningful production data source.

### Current modules

* `graph/graph\_builder.py`
* ingestion connectors already prototyped for ChEMBL, PubMed, OpenFDA, ClinicalTrials.gov

### Required changes

#### A. Build a disease-program-specific ETL pipeline

Do not ingest entire upstream sources. Build RA-centered filtered ingestion.

#### P0 sources

* ChEMBL: drug-target relations for RA-relevant drugs and targets
* ClinicalTrials.gov: RA interventional trials + candidate drug trial metadata
* PubMed: RA drug-disease literature for retrieval index

#### P1 sources

* OpenFDA: adverse event context
* Drug metadata source for approval / indication status

#### B. Create a graph schema implementation

Target node types:

* Drug
* Target
* Disease
* Trial
* Pathway (preferred in v2, acceptable slightly later)
* AdverseEvent (optional in early v2)

Target edge types:

* `TARGETS`
* `INDICATES`
* `TRIAL\_INVESTIGATES`
* `TRIAL\_CONDITION`
* `ASSOCIATED\_WITH`
* `PARTICIPATES\_IN`
* `PATHWAY\_DYSREGULATED`
* `CAUSES` (later if OpenFDA included)

#### C. Standardize provenance fields on every edge

All edges should carry:

* `source\_db`
* `confidence`
* `source\_record\_id`
* `evidence\_year`
* `pmid` where applicable
* `status` where applicable

#### D. Add graph build orchestration

Implement a reproducible build command such as:

* `python scripts/build\_ra\_program\_graph.py`

Pipeline steps:

1. fetch/parse source subsets
2. normalize entity IDs
3. map disease IDs
4. deduplicate entities
5. compute edge confidence
6. write nodes/edges to Neo4j
7. emit graph statistics report

#### E. Version graph snapshots

Each build should output:

* node counts
* edge counts
* counts per node type
* counts per edge type
* graph version ID / timestamp

### New files or refactors

* `ingestion/ra\_program/chembl\_ra\_loader.py`
* `ingestion/ra\_program/clinicaltrials\_ra\_loader.py`
* `ingestion/ra\_program/pubmed\_ra\_loader.py`
* `ingestion/normalization/entity\_mapper.py`
* `ingestion/normalization/disease\_mapper.py`
* `scripts/build\_ra\_program\_graph.py`
* `reports/graph\_stats.py`

### Definition of done

* Neo4j contains a real RA-centered graph.
* Graph has materially more than the seed graph.
* Provenance is present on every core edge type.
* Build script can be rerun cleanly.
* Graph stats report is generated automatically.

\---

## 6.3 Graph Querying and Path Exposure

### Goal

Make graph paths first-class evidence objects.

### Current modules

* `graph/path\_traversal.py`
* `graph/edge\_confidence.py`
* `graph/coverage\_report.py`

### Required changes

#### A. Support ordered path templates

Implement metapath-aware traversal with priority ordering.

P0 path types:

* Drug → Target → Disease
* Drug → Trial → Disease

P1 path types:

* Drug → Target → Pathway → Disease
* Drug → AdverseEvent → Disease-context safety note

#### B. Return structured path objects

Each path should include:

* `path\_type`
* `nodes`
* `edges`
* `path\_confidence`
* `source\_disease\_context`
* `provenance`

#### C. Add adjacency-disease labeling

If a path uses SLE, PsA, or Sjogren context, that must be visible and should not be silently treated as RA evidence.

#### D. Upgrade coverage reporting

Coverage report should summarize:

* graph density
* literature density
* trial density
* path diversity
* known limitations

### New files or refactors

* `graph/metapath\_registry.py`
* `graph/path\_ranker.py`
* update `path\_traversal.py`
* update `coverage\_report.py`

### Definition of done

* Query results expose 1–3 top supporting paths per candidate.
* Paths carry provenance and confidence.
* Coverage report is included in every accepted response.
* Adjacency-based evidence is visibly labeled.

\---

## 6.4 Ranking Engine Redesign

### Goal

Replace “GNN-led scoring” with interpretable composite ranking.

### Current modules

* `gnn/model.py`
* `gnn/data\_loader.py`
* `gnn/train.py`
* `gnn/inference.py`

### Required changes

#### A. Implement baseline ranking first

Baseline methods to implement before changing the GNN:

1. common-neighbor / shared-target score
2. weighted path count score
3. random baseline for sanity

#### B. Build a composite scorer

Composite score fields:

* `graph\_score`
* `evidence\_score`
* `trial\_score`
* `learned\_score`
* `composite\_score`

Initial weighting:

* graph score: 0.40
* evidence score: 0.25
* trial score: 0.20
* learned score: 0.15

#### C. Add novelty/status labeling

Every candidate must be labeled as one of:

* `known\_indication`
* `adjacent\_offlabel`
* `trial\_explored`
* `exploratory`

#### D. Keep GNN auxiliary

The current GAT remains in code but should be treated as:

* a plumbing-valid learned score provider
* retrainable component for later graph scale
* not the primary justification for any result

#### E. Add score component transparency

Each candidate should include component-level metadata:

* path count
* average path confidence
* literature chunk count
* trial count
* raw GNN score
* normalization note

### New files or refactors

* `ranking/baselines/common\_neighbor.py`
* `ranking/baselines/weighted\_path.py`
* `ranking/baselines/random\_baseline.py`
* `ranking/composite\_scorer.py`
* `ranking/novelty\_classifier.py`
* `ranking/score\_schema.py`
* update `gnn/inference.py`

### Definition of done

* Ranking works without requiring the GNN.
* Candidate list contains all component scores.
* Known therapies are labeled correctly.
* Baselines can be run from the same candidate pool.

\---

## 6.5 Retrieval Layer Redesign

### Goal

Make retrieval candidate-aware and evidence-supporting rather than generic semantic search.

### Current modules

* `rag/embedder.py`
* `rag/vectorstore.py`
* `rag/retriever.py`

### Required changes

#### A. Build a real index

Index RA-focused:

* PubMed abstracts
* ClinicalTrials.gov summaries

#### B. Add metadata-rich chunking

PubMed chunk metadata:

* PMID
* title
* year
* drug mentions
* disease mentions
* target/pathway mentions
* source type

Trial metadata:

* NCT ID
* title
* phase
* status
* disease condition
* intervention names

#### C. Candidate-aware query construction

For each candidate, generate three queries:

1. drug + disease + target/pathway + mechanism
2. drug + disease + trial
3. drug + disease + repurposing / repositioning

#### D. Deduplicate retrieval results

Multiple query runs should be merged and deduplicated by PMID / NCT ID.

#### E. Add weak/contradictory evidence handling

When evidence is sparse, negative, or contradictory, it should be surfaced as counter-evidence.

### New files or refactors

* `rag/indexers/pubmed\_indexer.py`
* `rag/indexers/trials\_indexer.py`
* `rag/query\_builder.py`
* `rag/evidence\_packet.py`
* update `retriever.py`

### Definition of done

* FAISS index contains meaningful RA-focused data.
* Retrieval is candidate-aware.
* Retrieved evidence objects contain metadata and relevance scores.
* Sparse or contradictory evidence can be surfaced explicitly.

\---

## 6.6 Explanation Layer Redesign

### Goal

Transform LLM output from free-form chain-of-thought into constrained evidence narration.

### Current modules

* `llm/client.py`
* `llm/chain\_of\_thought.py`
* `llm/safety\_filter.py`
* `llm/equity\_ranker.py`

### Required changes

#### A. Change explanation contract

The LLM should output structured JSON only:

* `structured\_summary`
* `plain\_language\_summary`
* `uncertainty\_statement`
* `basis`

#### B. Constrain prompt inputs

Prompt should consume only:

* candidate metadata
* score breakdown
* supporting paths
* retrieved literature
* trial evidence
* counter-evidence
* coverage limitations

#### C. Forbid unsupported synthesis

Hard prompt constraints:

* do not invent mechanisms
* do not add entities not supplied
* do not use clinical/prescriptive language
* explicitly state when evidence is sparse
* explicitly label known therapies as known

#### D. Safety filter remains, but downstream

Safety filter should validate generated structured summaries for forbidden language.

#### E. Demote equity ranker

Keep it out of core ranking for v2.
Possible v2 role:

* optional annotation field
* disabled by default

### New files or refactors

* `llm/prompts/explanation\_json\_prompt.txt`
* `llm/explanation\_schema.py`
* update `chain\_of\_thought.py` to structured-output mode
* update `safety\_filter.py`
* update / disable `equity\_ranker.py` in composite scoring path

### Definition of done

* LLM returns structured explanation JSON.
* Output contains explicit uncertainty.
* No free-form speculative biology is returned.
* Safety filter blocks clinical wording.

\---

## 6.7 Evaluation Framework

### Goal

Make evaluation runnable, visible, and integral to the build.

### Required changes

#### A. Build gold-standard RA set

Construct a public-data evaluation set with:

* approved RA therapies
* drugs tested in RA trials but not approved
* off-label / adjacent signals from public reviews

#### B. Support two evaluation modes

1. standard known-therapy recovery
2. novelty-aware hidden-edge recovery

#### C. Implement core metrics

Primary:

* Recall@10
* Recall@20
* MRR
* Novel candidate ratio

Secondary:

* explanation groundedness
* uncertainty honesty
* literature coverage
* adjacent discovery rate

#### D. Implement manual review protocol

For top results:

* verify path exists in graph
* verify PMIDs/NCT IDs exist
* compare explanation against supplied evidence
* flag hallucinated entities or relations

#### E. Emit evaluation reports

Evaluation report should contain:

* graph version used
* metrics
* baseline comparisons
* groundedness review
* known issues

### New files or refactors

* `evaluation/gold\_standard\_builder.py`
* `evaluation/mvp\_evaluator.py`
* `evaluation/ranking\_metrics.py`
* `evaluation/explanation\_review.py`
* `evaluation/error\_taxonomy.py`
* `scripts/run\_mvp\_evaluation.py`

### Definition of done

* One command runs an evaluation pass.
* Baseline and system metrics are reported side-by-side.
* Manual review template exists.
* Evaluation artifacts are saved to disk.

\---

## 6.8 API Integration and Response Assembly

### Goal

Return a stable, inspectable response contract from FastAPI.

### Current modules

* `api/main.py`
* response assembly logic

### Required changes

#### A. Implement formal response schema

Response sections:

* `query`
* `program\_scope`
* `coverage\_report`
* `candidates`
* `research\_only\_disclaimer`

#### B. Candidate object fields

Each candidate should include:

* drug name
* ranking scores
* novelty bucket
* supporting paths
* retrieved evidence
* counter-evidence
* explanation object

#### C. Add response validation

Use Pydantic or equivalent to validate outputs before return.

#### D. Add observability

Log:

* graph version
* retrieval hit count
* explanation generation time
* safety flag count
* total query time

### New files or refactors

* `schemas/response.py`
* `services/query\_pipeline.py`
* `services/candidate\_assembler.py`
* updates in `api/main.py`

### Definition of done

* FastAPI returns valid structured JSON.
* All candidate fields are present or explicitly null with reason.
* Logging allows debugging of failures.

\---

## 7\. Engineering Backlog by Priority

## P0 — Must do now

* Freeze disease-program config
* Freeze response schema
* Implement RA-focused data ingestion
* Build real Neo4j RA subgraph
* Implement path-based ranking baseline
* Implement candidate-aware retrieval
* Convert explanations to structured JSON
* Build evaluation scaffold
* Exclude GNN from primary ranking logic

## P1 — Important after P0

* Add pathway nodes and pathway-based paths
* Add trial evidence weighting and richer trial parsing
* Add contradiction detection rules
* Add OpenFDA adverse-event context
* Build manual review tooling

## P2 — Later

* Retrain GNN on larger graph
* Revisit equity ranker as optional view
* Add adjacency disease query expansion beyond RA-only input
* Add frontend beyond API usability

\---

## 8\. Suggested Repository Structure

```text
project-root/
├── api/
│   └── main.py
├── config/
│   └── disease\_program.yaml
├── schemas/
│   ├── query.py
│   ├── response.py
│   └── explanation.py
├── services/
│   ├── disease\_resolver.py
│   ├── query\_pipeline.py
│   └── candidate\_assembler.py
├── ingestion/
│   ├── normalization/
│   │   ├── entity\_mapper.py
│   │   └── disease\_mapper.py
│   └── ra\_program/
│       ├── chembl\_ra\_loader.py
│       ├── clinicaltrials\_ra\_loader.py
│       └── pubmed\_ra\_loader.py
├── graph/
│   ├── graph\_builder.py
│   ├── path\_traversal.py
│   ├── path\_ranker.py
│   ├── metapath\_registry.py
│   ├── edge\_confidence.py
│   └── coverage\_report.py
├── ranking/
│   ├── baselines/
│   │   ├── common\_neighbor.py
│   │   ├── weighted\_path.py
│   │   └── random\_baseline.py
│   ├── composite\_scorer.py
│   ├── novelty\_classifier.py
│   └── score\_schema.py
├── gnn/
│   ├── model.py
│   ├── data\_loader.py
│   ├── train.py
│   └── inference.py
├── rag/
│   ├── embedder.py
│   ├── vectorstore.py
│   ├── retriever.py
│   ├── query\_builder.py
│   ├── evidence\_packet.py
│   └── indexers/
│       ├── pubmed\_indexer.py
│       └── trials\_indexer.py
├── llm/
│   ├── client.py
│   ├── chain\_of\_thought.py
│   ├── safety\_filter.py
│   ├── equity\_ranker.py
│   ├── explanation\_schema.py
│   └── prompts/
│       └── explanation\_json\_prompt.txt
├── evaluation/
│   ├── gold\_standard\_builder.py
│   ├── mvp\_evaluator.py
│   ├── ranking\_metrics.py
│   ├── explanation\_review.py
│   └── error\_taxonomy.py
├── scripts/
│   ├── build\_ra\_program\_graph.py
│   └── run\_mvp\_evaluation.py
└── reports/
    └── graph\_stats.py
```

\---

## 9\. Exact Execution Tasks

## Task Group A — Freeze configs and schemas

### Tasks

* Create `disease\_program.yaml`
* Create `schemas/query.py`
* Create `schemas/response.py`
* Create `schemas/explanation.py`
* Encode novelty bucket enum
* Encode evidence tier enum

### Output expected

* committed config and schema files
* one example accepted query JSON
* one example rejected query JSON
* one example full response JSON

### Definition of done

* all downstream modules import schemas instead of using ad hoc dicts

\---

## Task Group B — Build RA graph pipeline

### Tasks

* implement RA subset extraction for ChEMBL
* implement RA trial extraction for ClinicalTrials.gov
* implement RA literature pull for PubMed
* normalize disease IDs to UMLS CUIs
* write graph build script
* emit graph stats summary

### Output expected

* reproducible graph build command
* Neo4j populated with real RA program graph
* graph stats artifact showing counts by entity and edge type

### Definition of done

* graph can be rebuilt from source scripts
* seed graph no longer acts as meaningful production dataset

\---

## Task Group C — Ranking overhaul

### Tasks

* implement path-count heuristic
* implement common-neighbor heuristic
* implement random baseline
* implement composite scorer
* add novelty classification
* expose component scores in candidate output

### Output expected

* candidate ranking table for RA query
* side-by-side scores for top candidates
* explicit known/adjacent/trial/exploratory labels

### Definition of done

* top candidate list can be generated without the GNN

\---

## Task Group D — Retrieval and evidence packets

### Tasks

* index PubMed abstracts
n- index trial summaries
* build candidate-aware retrieval query builder
* deduplicate retrieved evidence
* create evidence packet schema
* surface sparse or contradictory evidence flags

### Output expected

* top evidence packet for at least 5 candidates
* metadata-rich retrieved chunks
* counter-evidence examples in output

### Definition of done

* every top-ranked candidate has either evidence or explicit evidence sparsity note

\---

## Task Group E — Explanation refactor

### Tasks

* rewrite explanation prompt for structured JSON
* modify `chain\_of\_thought.py` to return structured fields only
* add explanation schema validator
* run safety filter post-generation
* add uncertainty statement rules

### Output expected

* explanation JSON for at least 5 candidates
* zero clinical language in generated summaries
* known therapies explicitly labeled as known

### Definition of done

* free-form chain-of-thought text is no longer returned by production API

\---

## Task Group F — Evaluation framework

### Tasks

* create RA gold-standard candidate list
* implement Recall@K and MRR metrics
* implement baseline comparisons
* add manual review worksheet / protocol
* generate evaluation report JSON or markdown

### Output expected

* one reproducible MVP evaluation run
* metric outputs for system and baselines
* manual review checklist for top-5 candidates

### Definition of done

* evaluation can be run on demand after graph build and indexing

\---

## Task Group G — API integration

### Tasks

* integrate disease resolver
* integrate graph query service
* integrate ranking service
* integrate retrieval and explanation services
* assemble response schema
* add structured logging

### Output expected

* one stable `/query` endpoint response for RA
* logs showing graph version, timings, and safety flags

### Definition of done

* system produces end-to-end structured response on live graph and live index

\---

## 10\. Suggested Execution Timeline by Dependency, Not Calendar

### Block 1 — Foundations

Complete first:

* disease config
* schemas
* graph schema
* response schema

### Block 2 — Real data substrate

Then complete:

* RA ingestion
* Neo4j population
* graph stats
* retrieval indexing

### Block 3 — Inspectable reasoning

Then complete:

* path traversal outputs
* baseline ranking
* novelty classification
* coverage reporting

### Block 4 — Controlled explanation

Then complete:

* evidence packets
* explanation JSON
* safety validation

### Block 5 — Evaluation and API hardening

Finally complete:

* metrics
* manual review
* evaluation artifacts
* endpoint stabilization

\---

## 11\. What to Defer Deliberately

The following should be explicitly postponed to avoid scope drift:

* full multi-disease support
* frontend redesign as primary focus
* broad OpenFDA integration before core ranking works
* equity-aware reranking in the main score
* claims of “novel discovery” behavior
* large-scale GNN retraining before real graph baselines are operational

\---

## 12\. Risks During Implementation

### Highest risk technical failures

* ingestion normalization fails due to inconsistent IDs
* graph remains too sparse to support diverse paths
* retrieval returns generic inflammation papers rather than candidate-specific evidence
* explanation prompt drifts into unsupported biology
* novelty bucket mislabels known RA drugs
* evaluation rewards memorization instead of plausible recovery
* Ollama becomes unstable under repeated structured-generation calls

### Mitigations

* keep disease scope hard-bounded
* validate entity mappings before graph writes
* inspect top retrievals manually early
* make explanations schema-validated
* keep novelty labeling rule-based at first
* compare all ranking outputs to simple baselines
* cache or batch LLM calls where possible

\---

## 13\. What Can Be Safely Claimed After v2

If the above plan is implemented successfully, defensible claims include:

* DRIPE is a research-only RA-focused drug repurposing system.
* It combines graph path evidence, literature/trial retrieval, and structured explanation.
* It returns inspectable candidate evidence packages rather than opaque scores alone.
* It includes baseline-based evaluation and uncertainty disclosure.

Claims that still should not be made after v2 unless separately proven:

* DRIPE discovers novel RA therapies.
* The GNN meaningfully outperforms interpretable baselines.
* The system is clinically useful.
* The system generalizes across autoimmune diseases.

\---

## 14\. Immediate Kickoff Checklist

Use this as the actual trigger list for the workflow.

### Today’s kickoff actions

* \[ ] Create and commit `config/disease\_program.yaml`
* \[ ] Create query/response/explanation schemas
* \[ ] Freeze novelty bucket enum and response contract
* \[ ] Implement RA-focused graph build script skeleton
* \[ ] Wire one real data source into Neo4j end-to-end
* \[ ] Implement one baseline ranker independent of GNN
* \[ ] Define evidence packet object
* \[ ] Rewrite explanation prompt to structured JSON
* \[ ] Scaffold evaluation runner

### First checkpoint outputs required

* graph schema file or documented implementation
* one RA graph build run summary
* one ranked candidate JSON response
* one evidence packet example
* one explanation JSON example
* one evaluation runner stub that prints placeholders or first metrics

\---

## 15\. Final Instruction

Do not try to make DRIPE look bigger during implementation.
Make it narrower, more inspectable, and more reproducible.

The correct engineering strategy is:

* real data over toy elegance,
* explicit evidence over fluent prose,
* baselines over model prestige,
* bounded scope over breadth,
* evaluation over demo theatrics.

That is what turns the current architecture into a credible RA-focused research platform.

