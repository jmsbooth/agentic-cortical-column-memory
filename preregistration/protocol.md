# CCM protocol v0.1.0

**Publication state:** architecture and preregistered evaluation framework
**Registration state:** frozen for public v0.1.0 after this conceptual revision
**Release:** v0.1.0 · September 2026 · James Booth · Independent researcher
**Peer review:** not peer reviewed

## Primary research question

Does structured modular world-state memory improve agent memory quality and downstream task performance compared with conventional memory architectures under matched history, task, model, and resource conditions?

## Research questions

1. **Memory quality:** Does CCM improve relevant-memory recall compared with conventional agent-memory architectures?
2. **State consistency:** Does CCM improve temporal, relational, and provenance consistency across long-running interactions?
3. **Reference frames:** Do explicit reference frames provide value beyond structured memory without frame constraints?
4. **Modular models:** Does partitioning memory into bounded local models reduce irrelevant-memory contamination compared with a flat structured store?
5. **Active acquisition:** Does active information acquisition resolve incomplete or contradictory memory state?
6. **Resource efficiency:** What latency, token, storage, compute, and coordination overhead does CCM introduce?
7. **Model-scale interaction:** Does the relative benefit vary across model capability classes?
8. **Multi-agent composability:** Exploratory only: can independent CCM-equipped agents exchange bounded memory-derived state without a globally shared memory store?

Model-scale and multi-agent questions are subordinate to the memory architecture question. The deterministic adapter is a software control, not a language-model benchmark.

## System under test

CCM is a model-agnostic, agent-internal memory architecture. A CCM column is not an agent; one agent may contain multiple columns, and multiple agents may each contain an independent CCM instance. Columns are bounded persistent modeling units that maintain local observations, relations, state, hypotheses, predictions, and reference-frame context.

The memory schema distinguishes:

- immutable externally acquired `Observation` objects;
- typed `Relation` objects;
- interpreted `State` objects;
- unconfirmed `Hypothesis` objects;
- validated or hypothesized `Transition` objects; and
- derived `Prediction` objects.

Historical observations are never overwritten. Current state is derived separately and may use `valid_from`, `valid_to`, `superseded_by`, observed time, recorded time, and explicit late-arrival handling.

The agent-facing interface is `recall(query, current_context, budget)`. It returns a bounded context containing relevant state, supporting observations, temporal context, provenance, unresolved conflicts, hypotheses, confidence, and optional evidence gaps. Reconciliation classifies local states as agreement, complementary, contradiction, unresolved, or unknown. Structured quorum voting is one optional downstream algorithm, not the definition of CCM.

CCM does not model cortical biology and does not claim equivalence between software modules and biological cortical columns. TPAA is not required; CCM may be embedded in TPAA or another agent framework.

## Primary baselines

- **M0:** no persistent memory; current task context only;
- **M1:** full-history memory;
- **M2:** summarized memory;
- **M3:** vector-similarity memory;
- **M4:** structured key/value or episodic memory;
- **M5:** knowledge-graph memory where practical;
- **M6:** full CCM;
- **M7:** CCM plus an optional ontology substrate, exploratory if implemented.

Registered CCM ablations are `CCM-NoRF`, `CCM-NoModules`, `CCM-NoTemporal`, `CCM-NoReconciliation`, `CCM-NoActive`, and `CCM-FlatLedger`. Majority vote, debate, self-consistency, and answer aggregation remain secondary composition/inference experiments.

## Task suite

The versioned deterministic suite contains persistent factual recall, temporal state, relational recall, conflicting evidence, state replacement/supersession, provenance recall, cross-frame integration, distractor resistance, long-horizon continuity, active evidence, incomplete information, and pure reasoning control. Every task has a stable ID, hidden answer, candidate hypotheses, provenance-bearing observations or actions, and explicit required evidence where applicable.

## Resource accounting

Every task record includes input/output tokens, model invocation count, wall-clock latency, communication bytes, bytes stored, object and relation counts, index size, recall candidates examined, context tokens produced, retrieval CPU/wall time, and memory-update cost. CPU/GPU utilization, accelerator time, energy, and API cost are `null` with a measurement note when unavailable.

The registered analysis reports memory quality against storage, retrieval latency, context, and compute. It does not credit additional model calls as a memory improvement without matched-budget analysis.

## Statistical analysis

The unit of analysis is a task instance. The registered configuration uses three independent seeds and ten instances per task class. Primary comparisons are paired by task ID and seed. Report raw differences, 95% percentile bootstrap confidence intervals using 10,000 resamples, paired effect sizes, and Holm correction across the primary confirmatory tests. A minimum practically meaningful difference is 0.05 on the relevant bounded metric. Failures and timeouts remain in denominators. No silent outlier removal or outcome-dependent stopping is permitted.

## Negative-results policy

All registered seeds, task instances, failures, contradictions, unresolved states, abstentions, and unavailable resource fields are retained. Unsupported hypotheses, neutral results, and harmful components are reportable outcomes. Smoke artifacts validate software behavior only and cannot replace the registered campaign.

## Provenance and privacy

Run manifests identify configuration, model/task versions, seed, hardware, timestamp, Git commit, raw output, and result hash. Structured traces are the audit surface; private chain-of-thought is neither required nor stored. Secrets, credentials, raw sensitive payloads, and PII are out of scope.

## Deviations and versions

This revision is the conceptual correction before public v0.1.0. After publication, material changes to hypotheses, primary metrics, task-generation logic, baselines, exclusions, or statistical thresholds require a protocol deviation note and a new protocol version. Corrections that do not alter registered methodology may use a v0.1.x release with a changelog entry.
