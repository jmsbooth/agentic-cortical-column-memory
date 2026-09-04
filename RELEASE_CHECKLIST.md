# v0.1.0 release checklist

## Paper and claims

- [x] Title and abstract describe an architecture/protocol release.
- [x] Authorship, date, version, repository, license, and peer-review status are explicit.
- [x] No fabricated registered result is reported.
- [x] TBT, TBP/Monty, HTM, and CCM are distinguished.
- [x] Reference frames, columns, memory, voting, active evidence, invariants, and termination are defined.
- [x] Hypotheses, baselines, ablations, metrics, resource controls, statistics, threats, and negative-results policy are registered.
- [x] `paper/build/main.pdf` compiles from source after the local LaTeX toolchain is available.

## Repository and validation

- [x] Reference implementation and deterministic task worlds are present.
- [x] Run manifests and provenance-bearing JSONL traces are generated.
- [x] Unit, integration, invariant, regression, and smoke tests are present.
- [x] GitHub Actions runs tests, smoke validation, static compilation, and paper checks.
- [x] README and reproduction guide document clean-checkout execution.
- [x] `CITATION.cff`, code license, paper license, and changelog are present.
- [x] Smoke output is the only committed result artifact and is labelled as software validation.

## Before publishing the tag

- [ ] Review the generated PDF and the final diff.
- [ ] Run `git diff --cached --check` after staging.
- [ ] Tag the exact paper/repository commit as `paper-v0.1.0`.
- [ ] Create a GitHub release containing the PDF, source, protocol, configs, smoke output, and checksums.
- [ ] Add a permanent archive DOI in a later manuscript version if one exists.
- [ ] Update the website with status `Architecture and Registered Evaluation Protocol` and `Peer Review: Not peer reviewed`.
