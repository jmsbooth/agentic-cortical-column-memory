# Experiment guide

The evaluation is memory-first. Model-scale and multi-agent inference are secondary dimensions, not the identity of CCM.

## Primary memory matrix

| ID | Definition |
| --- | --- |
| M0 | No persistent memory; current task context only |
| M1 | Full-history memory |
| M2 | Summarized memory |
| M3 | Vector-similarity memory |
| M4 | Structured key/value or episodic memory |
| M5 | Knowledge-graph memory |
| M6 | Full CCM |
| M7 | CCM plus an optional ontology substrate; planned exploratory extension |

The dependency-free smoke adapter implements transparent symbolic stand-ins for M0–M6. It does not claim to implement a learned summarizer, embedding model, or production knowledge graph.

## CCM ablations

| ID | Removed mechanism |
| --- | --- |
| `CCM-NoRF` | Explicit reference-frame constraints |
| `CCM-NoModules` | Multiple bounded columns; one local module remains |
| `CCM-NoTemporal` | Temporal recall/state constraints |
| `CCM-NoReconciliation` | Reconciliation-driven structured commit |
| `CCM-NoActive` | Active evidence acquisition |
| `CCM-FlatLedger` | Frame-aware organization; flat ledger comparison |

Legacy B0–B5 inference/composition strategies remain available for exploratory secondary runs but are not the primary CCM benchmark.

## Task classes

The versioned synthetic suite covers persistent factual recall, temporal state, relational recall, conflicting evidence, state replacement/supersession, provenance recall, cross-frame integration, distractor resistance, long-horizon continuity, active evidence, incomplete information, and pure reasoning control.

## Primary metrics

- recall precision and recall;
- state reconstruction accuracy;
- temporal accuracy and stale-state rate;
- relation accuracy;
- provenance accuracy;
- contradiction preservation;
- false-memory and unsupported-memory rates;
- relevant-context density and context tokens;
- retrieval latency, update latency, storage bytes, relation count, index size, and candidates examined;
- downstream task success as a secondary outcome.

## Required provenance

Each record carries observations, current/recalled state, provenance, relations, hypotheses, predictions where present, reconciliation, actions, final status, failure category, resource usage, configuration hash, Git commit, model version, task version, hardware, timestamp, and seed. Intermediate model reasoning is not required; explicit structured artifacts are the audit surface.

## Statistical controls

The unit of analysis is a task instance. The preregistration specifies paired task/seed comparisons, bootstrap confidence intervals, effect sizes, Holm correction, practical significance, no silent outlier removal, no outcome-dependent stopping, and failures/timeouts retained in denominators. Pareto analysis compares memory quality against storage, retrieval latency, context, and compute.
