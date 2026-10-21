# CCM-EMP-002 Phase 1A: local validation evidence

**Classification:** Targeted software-validation evidence only; not empirical CCM performance.
**Observed run:** 2026-10-21 20:37:50Z through 20:37:54Z UTC.
**Source branch head during tests:** `c1ebff174bf95726ffd307ac6e83578353bdcdb1`.
**Runtime:** Linux x86_64, Python 3.13.5.
**Protocol:** `CCM-EMP-002`, prospective v0.2.0, sha256 `e583099d7b2bdd8b0d56eda83e620c24a063eeeeaee1c5cc4f1ebb1d035d60b6`.

## Executed commands

| Command | Exit code | Outcome |
| --- | ---: | --- |
| `python3 -m compileall -q ccm/empirical ccm/adapters/empirical.py evaluation/empirical experiments/empirical` | 0 | PASS |
| `python3 -m unittest discover -s tests -t . -v` (new Phase 1A subset) | 0 | PASS, 18 tests |
| `./scripts/ccm_preflight --config experiments/configs/smoke_v0.1.0.json` (local shape fixture) | 0 | PASS, software-validation classification |
| `./scripts/ccm_preflight --config preregistration/registered-configs/ccm-v0.1.0.json` (local shape fixture) | 2 | PASS, blocked as required |
| `./scripts/ccm_preflight --config experiments/configs/real_model_unqualified_preflight.json` (local shape fixture) | 2 | PASS, blocked as required |

The local preflight shape fixtures contain only the fields used by the new gate. The legacy registered configuration in the repository contains the same `run_kind`, symbolic model identity, and unqualified M0-M6 baseline choices. The exact repository-wide smoke and runner suites were **not** executed in this environment.

### Observed blocked controls

- `baseline_fidelity`: no M0-M6 implementation in the baseline registry is yet qualified for empirical evaluation.
- `real_model_required`: the v0.1.0 `toy-symbolic-v0.1.0` model is ineligible for empirical runs.
- `registered_runner_qualified`: the legacy `experiments.runners.run` may only produce software validation, not model effectiveness measurements.
- Even with an otherwise admissible model family, an unfitted baseline and unqualified runner cause the preflight to reject execution.

### Confirmed source integrity

The newly added model/evaluator boundary, operations plans, preflight module, baseline registry, fixture generator and tests were checked against their corresponding GitHub Git blob SHAs. All 12 new source/test files matched the branch after publishing.

## Outstanding evidence gates

**BLOCKED: Complete repository checkout.** This execution environment could not resolve `github.com`, so a clean clone and full exact-head test run could not be performed.

**BLOCKED: Legacy repository smoke integration test.** Existing smoke fixtures and legacy runner imports were unavailable locally. A positive targeted preflight is not a substitute for that integration run.

**NOT RUN: Empirical CCM effectiveness.** No pilot, model-backed memory comparison or confirmatory benchmark was executed.

This increment is **not qualified for merge** until a complete checkout passes existing unit, integration, regression, negative and smoke gates and their locally captured logs are committed.

## SHA-256 of complete local output logs

```text
e9f34c4ff5f840030070b909836a230cab3b553e2cdbfbfa27334aadab7cbab2  compile.log
1032d35785f6b05582d0f086eda15a912ffd3c26db009732bc446bd88f9bdf37  preflight-legacy-registered.log
52719484c0b8075bdaeb35ac70fe96ad6c793da7ef56256822b354055d1dbca5  preflight-real-unqualified.log
c8ad625f1db98f03f023f2e6b16521d4bc12f1384e5b10c4a548d391698dc7fd  preflight-smoke.log
8bc6fef574c3c6e5039692645a5c6cbc26a6b7608ade39596ecb8633bddbfd10  unit-invariant.log
```

Log files with these digests exist in the local execution workspace. This report preserves their outcomes and digests, but **does not claim those logs were committed to GitHub**. Complete evidence publication remains an acceptance task in Issue #2.
