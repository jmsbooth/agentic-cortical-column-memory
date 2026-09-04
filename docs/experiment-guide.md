# Experiment guide

The protocol separates architectural improvement from inference scaling.

## Matrix

| ID | Definition |
| --- | --- |
| B0 | One small-model direct inference |
| B1 | One small model with equivalent context/memory |
| B2 | Self-consistency over independent samples |
| B3 | Conventional multi-agent inference without aggregation |
| B4 | Conventional majority vote |
| B5 | Answer-level confidence-weighted aggregation |
| CCM-Full | Reference frames, structured memory, distributed hypotheses, active evidence, structured consensus, specialization |
| CCM-NoRF | Remove explicit frame constraints |
| CCM-NoActive | Remove active evidence acquisition |
| CCM-NoVote | Commit from a single highest-confidence column |
| CCM-NoStructuredMemory | Disable append-only structured retrieval |
| CCM-NoSpecialization | Use a shared column specialization |

## Task classes

The synthetic suite includes persistent memory, multi-hop evidence, active acquisition, ambiguity resolution, tool use, long-horizon state, conflicting evidence, incomplete information, and pure reasoning. The pure-reasoning control is expected to reveal cases where architecture cannot substitute for model capability.

## Required provenance

Each record carries the task prompt and ground truth, column states, observations, memory operations, actions, hypotheses, votes, final status, metrics, failure category, resource usage, configuration hash, git commit, model version, task version, hardware, timestamp, and seed. Intermediate model reasoning is not required; explicit structured artifacts are the audit surface.

## Resource and statistics plan

The harness records tokens, invocations, latency, communication, and explicit unavailable fields for hardware energy metrics. The registered analysis reports unconstrained and budget-controlled views, including a capability/resource Pareto frontier. The unit of analysis is a task instance; seeds are independent runs. The preregistration specifies bootstrap confidence intervals, paired seed/task comparisons, Holm correction, minimum meaningful effect size, timeout/failure handling, and no post-hoc stopping.
