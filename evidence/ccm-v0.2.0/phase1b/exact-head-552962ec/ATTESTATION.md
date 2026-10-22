# CCM-EMP-002 Phase 1B: exact-head local qualification

**Status: PASS, source commit `552962ec4c99efe771fdb24e6db009b9bb3d1f75`.**

The repository was cloned locally from a checksum-verified, full Git bundle exported at the identified commit. `git rev-parse HEAD` matched the exported identifier. The existing exact-head worktree runner executed all eight required regression stages in a disposable local Git worktree; all stages passed.

The full Python test discovery included **90 passing tests**, including persistent SQLite observations, cross-process crash/restart recovery, transaction rollback, isolated namespaces, bitemporal state, known-at boundaries, schema integrity, model-visible ingress, actual CCM engine memory injection, and the new future-effective supersession regression. The runner also verified deterministic smoke records and the intended rejection of nonempirical registered runs.

An additional temporal defect was reproduced before this qualification: both the SQLite and in-memory implementations prematurely hid the old current record when supersession was scheduled for a future world-time instant. Both were corrected; the two new regression tests pass in the actual source checkout. Earlier scaffold-based tests do not count as this acceptance evidence.

`manifest.json` identifies start/end UTC, host runtime, test commands, expected and actual exits, and test count. `SHA256SUMS.txt` covers the nine unmodified raw evidence files. Verify with `sha256sum -c SHA256SUMS.txt` in this directory.

The source-export workflow run was https://github.com/jmsbooth/agentic-cortical-column-memory/actions/runs/39787078969. GitHub Actions packaged Git history for transfer only; **the validation ran locally**, not on GitHub Actions. The evidence-only PR is deliberately separated from the source PR to preserve the exact tested source commit.

**No empirical study or comparative memory-quality experiment has been executed.** The v0.2.0 protocol remains prospective.
