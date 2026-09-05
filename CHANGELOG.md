# Changelog

## v0.1.0 pre-publication revision — September 2026

Conceptual correction before the public tag, following `SPEC-CCM-PUBLICATION-001`:

- Recentered CCM on model-agnostic, agent-internal structured memory rather than small-model or multi-agent capability recovery.
- Added typed relations, interpreted state, predictions, temporal validity, supersession, bounded recall, context assembly, reconciliation outcomes, and a provider-neutral model adapter interface.
- Replaced the primary evaluation hierarchy with M0–M6 memory baselines and registered memory-focused ablations, tasks, metrics, and hypotheses.
- Added separate architecture/reference-frame/memory documentation and revised the README, manuscript metadata, and canonical repository references.
- Kept multi-agent and model-scale comparisons as secondary research dimensions and retained the deterministic toy adapter as a software control.

## v0.1.0 — 2026-09-03

Initial public protocol release. Material changes from the supplied manuscript:

- Reframed the work as a systems architecture and preregistered evaluation protocol, not a completed empirical study.
- Replaced the implementation-heavy title and corrected authorship and publication metadata.
- Defined explicit reference frames, columns, memory objects, structured votes, active evidence actions, invariants, failure taxonomy, and termination outcomes.
- Added registered baselines B0–B5, CCM component ablations, task classes, compute/resource accounting, statistical rules, and a negative-results policy.
- Added a dependency-free Python reference implementation, deterministic synthetic worlds, run manifests, JSONL traces, metrics, tests, CI, and reproduction scripts.
- Added a canonical architecture diagram, algorithm description, related-work and novelty matrix, threat analysis, licenses, citation metadata, and release checklist.
- The only checked-in measurements are deterministic software smoke-test artifacts; the registered empirical campaign remains pending.
