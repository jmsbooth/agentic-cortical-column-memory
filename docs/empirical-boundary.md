# CCM-EMP-002 Phase 1A: Model/evaluator boundary

**Scope:** Implementation preflight only. This document and the associated tests are **not** a model benchmark or a claim of memory effectiveness.

## Known baseline defects (frozen snapshot)

- Original review base SHA: `9ca43aaf70ca6542461ea95accf353a35af3d9f5`.
- Prospective protocol publication SHA: `24bc8cab3ecdcda56317acca43ef1ab6b9c26696`.
- The legacy `ToyModel._pick_without_evidence` in `experiments/baselines/strategies.py` reads `task.answer`.
- Legacy `SyntheticTask.candidate_answers` places the correct answer first.
- Legacy synthetic observations use `supports=<answer>` features.
- M3, M4, M5 are symbolic stand-ins, not faithful vector, episodic, or KG baselines.
- Legacy `CCMEngine.solve` creates an in-memory store per task; durable memory is Phase 1B.

These behaviors remain available **only for explicitly identified software smoke validation**. An invocation marked `registered`, `pilot`, `empirical`, or `confirmatory` must fail before legacy model generation.

## Authorized separation

The model-visible API is `ccm.empirical.contracts.ModelVisibleCase` with explicitly allowlisted fields. Input observations and source IDs are case-scoped; candidate options are shuffled using the opaque case identity rather than gold. JSON deserialization rejects unexpected or duplicate keys, unsupported labels and cross-case identities. The empirical model adapter accepts exactly `ModelVisibleCase` and validates the returned citation IDs.

Ground truth, acceptable answers, hidden task families and scoring metadata are owned by `evaluation.empirical.oracles.EvaluatorOnlyCase`. Its data is never serialized by the model-visible type and its module is banned from empirical model-path imports. The deterministic preflight fixture changes evaluator gold while holding visible case identity and history fixed; output bytes remain unchanged. **This is a boundary test, not an evidence that a real hosted model has been run.**

The generated preflight fixture is for inspecting the boundary only, not part of future held-out study tasks. Avoid reusing fixture histories in either pilot or confirmatory experiments. A truthful natural-language observation can reveal the answer as relevant evidence; the requirement prohibits **oracle labels** and grade fields, not legitimate task evidence.

## Preflight disposition

- `./scripts/ccm_preflight --config experiments/configs/smoke_v0.1.0.json` may pass with classification `software_validation_only`.
- `./scripts/ccm_preflight --config preregistration/registered-configs/ccm-v0.1.0.json` must exit nonzero because the old registered config uses the symbolic model and placeholder baselines.
- Even a real model identifier must be blocked until baseline fidelity is independently qualified and the dedicated empirical runner is audited.
- The legacy runner itself rejects every non-smoke configuration, so bypassing the wrapper script does not create apparent registered results.

## Evidence policy and limitations

All runs for Phase 1A must record exact invocation, status, environment, code commit, test names/count, log, and SHA-256 digests. Failed and blocked checks remain visible. The initial implementation can be unit-tested offline, but completing the full repository-wide regression gate requires a local checkout of the exact GitHub branch. If the runtime cannot obtain that checkout, record `BLOCKED` and keep the pull request open. Do not substitute a GitHub Actions run or a previous smoke result for that gate.
