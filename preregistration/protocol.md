# CCM protocol v0.1.0

**Publication state:** architecture and preregistered validation framework.<br>
**Registration state:** frozen before the full empirical campaign.<br>
**Release:** v0.1.0 · 2026-09-03 · James Booth

## Research questions

1. Can explicit modular memory, navigable reference frames, distributed hypothesis formation, active evidence gathering, and structured consensus recover capabilities that would otherwise require a larger model under local resource constraints?
2. Does CCM outperform conventional small-model inference techniques when total inference budget is controlled?
3. Which CCM mechanisms explain any improvement, and where does the architecture fail to compensate for base-model limitations?

## Registered claims

The hypotheses in [`hypotheses.yaml`](hypotheses.yaml) are the authoritative H1–H6 specification. No full-campaign result is claimed in v0.1.0. The negative-results policy is binding: all registered seeds and task instances are retained, and unsupported hypotheses or unhelpful components will be reported.

## System under test

CCM is a software architecture, not a biological model. A column is a local model plus state. A reference frame is a navigable state space with an identity, current location/state, observations, and validated transitions. Memory is an append-only collection of structured observations. A vote references a structured hypothesis and its evidence. The active policy selects an available observation/action by expected information gain per cost. The engine may commit, abstain, or remain unresolved.

The v0.1.0 executable harness uses `toy-symbolic-v0.1.0` only for deterministic software validation. A future model campaign must identify the model family, exact revision, quantization, prompt/template, runtime, and hardware in its manifest. A model-generated statement cannot be recorded as an externally observed fact.

## Baselines and ablations

The registered matrix is:

- B0: one small model, direct inference.
- B1: one small model with equivalent context/memory.
- B2: self-consistency across independent samples.
- B3: conventional multi-agent inference without aggregation.
- B4: conventional answer-level majority vote.
- B5: answer-level confidence-weighted aggregation.
- CCM-Full: reference frames, structured memory, distributed hypotheses, active evidence, structured consensus, and specialization.
- CCM-NoRF, CCM-NoActive, CCM-NoVote, CCM-NoStructuredMemory, CCM-NoSpecialization: one component removed at a time.

All strategies run on the same task instances, seeds, model adapter, and documented budgets. A capability improvement that disappears after matching call, token, latency, cost, or energy budgets is not credited as an architectural gain.

## Task suite

The versioned synthetic suite contains persistent memory, multi-hop evidence integration, active information acquisition, ambiguous hypothesis resolution, deterministic tool use, long-horizon state, conflicting evidence, incomplete information, and a pure reasoning control. Each task has hidden ground truth, candidate hypotheses, explicit evidence actions, and a stable task ID. External web retrieval is not part of the primary suite.

## Resource accounting

Every task record includes input/output tokens, model invocation count, wall-clock latency, communication bytes, and fields for CPU/GPU utilization, peak memory, accelerator time, energy, and API cost. Metrics unavailable on the execution host are recorded as `null` with a measurement note. The analysis must report both unconstrained capability and budget-controlled results, including a capability/resource Pareto frontier.

## Statistical analysis

The unit of analysis is a task instance. The registered configuration uses three independent seeds and ten instances per task class. Primary comparisons are paired by task ID and seed. Report raw differences, 95% percentile bootstrap confidence intervals using 10,000 resamples, and an effect size (paired success-rate difference; for continuous metrics, paired standardized mean difference). Use Holm correction across the five primary pairwise hypothesis tests. A minimum practically meaningful difference is 0.05 absolute task-success rate. Bounded outcomes are not assumed to be normally distributed.

Failures and timeouts remain in the denominator for task success. Invalid manifests or missing traces invalidate a run rather than silently dropping a task; the invalid-run reason is reported. No outlier removal is permitted. There is no early stopping based on observed outcomes. Exploratory analyses are labelled as such and cannot modify H1–H6.

## Provenance and privacy

The result JSONL contains structured states and artifacts, not private chain-of-thought. Every record links to a configuration hash, git commit, model/task versions, seed, hardware, timestamp, observations, actions, hypotheses, votes, final status, and resource record. Secrets, tokens, credentials, raw sensitive payloads, and PII are out of scope and must not be added.

## Deviations and versions

The v0.1.0 files are the frozen protocol. Corrections that do not alter hypotheses, metrics, baselines, exclusions, or thresholds may be released as v0.2.x with a changelog entry. Any change to those registered elements requires an explicit deviation record before collection and a new protocol version. A completed registered result release is v1.0.0 only after all seeds, raw data, generated tables/figures, confidence intervals, effect sizes, matched-budget comparisons, ablations, and failure analyses are present.
