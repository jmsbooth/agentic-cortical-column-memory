# CCM Empirical Validation Protocol

**Protocol ID:** CCM-EMP-002  
**Draft version:** 0.2.0, prospective and not yet frozen  
**Date:** 2026-10-21  
**Research artifact:** Cortical-Column Memory (CCM)  
**Repository at review:** `jmsbooth/agentic-cortical-column-memory`, `main` at `9ca43aaf70ca6542461ea95accf353a35af3d9f5`  
**Study classification:** Independent, preregistered, comparative systems experiment  
**Status:** Protocol only. No results are asserted by this document.

## 1. Research objective and decision standard

The primary question is whether CCM, as **a modular persistent-memory subsystem inside an individual agent**, improves the correct use of historical information compared with credible alternative memory systems. This is not a test of whether several agents can defeat a frontier model. Multi-agent composition and model-scale interactions are secondary studies.

The evaluation must permit four outcomes: **benefit**, **harm**, **practical equivalence**, and **inconclusive evidence**. Failure to reject a null hypothesis is not proof of equivalence. A positive result must not be credited to CCM when attributable to extra inference, stronger preprocessing, leaked labels, different information exposure, or a weak comparator.

The v0.1.0 preregistration and historical smoke artifacts remain unchanged. Before accessing confirmatory outcomes, create and freeze a *new* v0.2.0 protocol, explaining that it supersedes the earlier, unexecuted, model-agnostic symbolic protocol. Preserve and link both versions. Do not retroactively claim v0.1.0 registered an experiment it did not specify.

## 2. Experimental boundaries

**Software verification:** unit, integration, property, security, durability, and metamorphic tests. These establish that the implementation obeys its stated contract, not that it has better memory.

**Mechanism validation:** controlled synthetic tasks with hidden ground truth and *real model inference*, designed to isolate temporal state, reference frames, modularity, reconciliation, and recall. These can support bounded mechanistic conclusions, not unrestricted real-world claims.

**Confirmatory effectiveness:** a locked, independent held-out set of histories and questions. All memory systems receive equivalent information and use the same agent model and output schema. This is the only tier for primary statistical claims.

**External generalization:** run one or more preselected published benchmarks without tuning on their test labels, then an optional realistic agent workload. Report these separately from confirmatory results.

A **column is not an agent**. CCM columns are internal memory/modeling units. The outer agent, model, policy, tools, and reasoning prompt are held constant. One agent is paired with one memory system per experimental condition. Cross-agent orchestration must not contaminate the primary comparison.

## 3. Explicit questions and hypotheses

**Primary estimand:** the paired difference in **Grounded Resolution Accuracy (GRA)** between full CCM (M6) and the strongest eligible conventional memory baseline selected using development/pilot data **before** the confirmatory set is unsealed. Evaluate across independent histories/scenarios, not merely repeated queries from the same history.

GRA is the fraction of scored questions for which the system either (a) gives an accepted correct answer accompanied by an admissible sufficient evidence citation drawn from the ingested history, or (b) correctly abstains when the locked answer key identifies a genuinely unanswerable question. A wrong answer, unsupported citation, fabricated source, inappropriate abstention, timeout, or protocol failure scores zero. Gold answers must specify acceptable variants and alternative sufficient evidence paths. All systems receive source identifiers and the same JSON answer/citation/abstention schema.

Primary confirmatory contrast: **H1:** `GRA(CCM) - GRA(strongest eligible baseline) > 0`. The minimum practically important improvement is **5 percentage points**. Five points is a prospective practical decision threshold, not an assertion about expected performance.

Secondary hypotheses (all clearly designated confirmatory or exploratory in the locked registration):

- **H2:** CCM improves temporal and supersession accuracy relative to the strongest temporal baseline.
- **H3:** CCM improves provenance correctness and evidence recall without increasing fabricated-memory rate.
- **H4:** explicit reference frames add value over an otherwise identical CCM-NoRF condition.
- **H5:** distinct bounded columns add value over CCM-NoModules at equal resource budgets.
- **H6:** reconciliation lowers contradictory/unsupported memory presentation relative to CCM-NoReconciliation.
- **H7:** CCM changes context-efficiency and retrieval/storage cost compared with conventional methods.
- **H8 (exploratory):** the direction and magnitude of CCM's benefit vary by model class.
- **H9 (exploratory):** active acquisition and multi-agent CCM composition contribute incremental benefits in task environments that permit them.

Do not combine all secondary endpoints into a post hoc global score. Preserve separate success, abstention, evidence, resource, and failure outputs.

## 4. Non-negotiable validity repairs before data collection

1. **Eliminate oracle leakage.** In the current symbolic harness, `ToyModel` can access `task.answer`, the correct candidate is constructed first, and observations encode `supports=<answer>`. Keep these mechanisms only for isolated deterministic software tests. A real model, retriever, indexer, memory transformer, column, and context assembler must not receive answer keys, answer-aligned support tags, evaluator-only evidence IDs, or correct-candidate ordering. Enforce separate model-visible and evaluator-only task schemas and test this separation automatically.
2. **Make memory durable.** CCM must ingest a sequence, persist it to storage, close, restore from a new process/session, and answer later queries without rereading the original history from the test harness. Include crash/restart, versioning, isolation, and late-arriving-data tests.
3. **Implement actual comparators.** Present M3 must be backed by genuine embedding/vector search, M4 by a real episodic/key-value memory, and M5 by an actual graph traversal/relationship memory. The current shared symbolic placeholder is valid only for smoke testing. Add a strong lexical BM25/FTS baseline and a competitive temporal graph baseline to avoid measuring CCM against artificially weak alternatives.
4. **Prove ablation fidelity.** Removing a feature must remove its operational effect throughout ingestion, storage, recall, and response generation. For example, CCM-NoRF must remove frame-based lookup/transition constraints, not merely alter a final voting key. Include a differential test for every ablation.
5. **Fix correctness issues.** Validate historical as-of queries after later supersession; use parsed UTC timestamps rather than raw string ordering; detect invalid supersession cycles; reject cross-history and cross-tenant reference reuse; enforce hard context limits using the *actual model tokenizer*, not `.split()`; and ensure provenance and support metrics are calculated from actual returned evidence rather than generic nonempty fields.
6. **Separate measurement and inference.** A grader must never receive an experimental condition's identity while adjudicating ambiguous answers. The scoring system must never pass gold labels back to the agent.

**Gate:** no empirical result may be labeled confirmatory until these checks pass. Preserve the existing smoke outputs under `software_validation`, not `scientific_evidence`.

## 5. Test conditions and comparators

Each condition receives identical raw histories, timestamps, entity identifiers, user question, allowed tools, answer schema, model checkpoint, decoding configuration, and resource ceilings. The *memory implementation* is the manipulated variable.

| ID | Experimental memory condition | Requirement |
| --- | --- | --- |
| M0 | No persistent memory | Negative control; only current question |
| M1 | Full chronological history | Run within available context and report overflow; include an unconstrained long-context view when feasible |
| M2 | Competent rolling summary | Real summarization, tuned on pilot only; provenance IDs retained when possible |
| M3a | BM25/FTS text retrieval | Strong lexical baseline |
| M3b | Embedding/vector RAG | Actual embeddings, indexing, top-k, and metadata filters |
| M4 | Structured episodic/key-value memory | Real updates, retrieval, time and source support where applicable |
| M5 | Temporal knowledge graph | Actual relation storage and graph traversal; support bitemporal state where feasible |
| M6 | Full CCM | Multiple internal columns, frames, temporal state, recall, reconciliation |
| Optional | Mature published agent-memory system | Pin version and configure fairly if feasible |

Include a **diagnostic oracle-retrieval upper bound** where the answer model receives only correct supporting evidence selected by the evaluator. This is a sensitivity check on the question/reader, not a competing memory system and never available to CCM or baseline ingestion. Include straightforward positive-control episodes where valid history plainly contains the answer.

Ablations: `CCM-NoRF`, `CCM-NoModules`, `CCM-NoTemporal`, `CCM-NoReconciliation`, `CCM-NoActive`, `CCM-FlatLedger`. Include a **single structured, temporally aware store without columns** as a strong diagnostic control; it tests whether the architectural modularity itself adds benefit above modern data modeling.

Use the strongest baseline **selected from pilot performance**, rather than whichever baseline is easiest for CCM to beat. Preserve all other comparisons in the output and apply multiplicity correction to designated secondary contrasts.

**Fairness distinction:** All methods see the same raw evidence; they may perform their own ingestion/indexing, but every model call and transformation cost is measured. A separate *representation-parity diagnostic* can supply common normalized events to structured baselines and CCM, allowing the effects of reference-frame/reconciliation mechanics to be isolated from information-extraction quality. Do not silently provide CCM oracle-enriched graphs that the baseline must infer from text.

## 6. Models, prompts, tools, and resource budgets

Use one preselected **anchor language model** for the confirmatory comparison, chosen by feasibility and a pilot conducted without confirmatory-label access. All primary conditions must use the **same model revision**, tokenizer, quantization, decoding settings, system prompt, tool permissions, and answer format. The CCM columns may use shared calls to that model but may not be counted as distinct independent agents.

Secondary portability runs use a second, materially different model class and, if feasible, a frontier reference. They are exploratory unless separately powered and frozen. Do not compare different backbone models as though their memory systems caused the difference.

Report two resource regimes:

1. **Matched-budget:** common upper bounds on retrieved memory-context tokens, answer-generation tokens, wall time, and optional model calls. Pre-register the budget grid in actual tokenizer units before confirmatory runs. The primary budget is selected using development/pilot data only.
2. **Cost/quality frontier:** measure the actual benefit obtained as memory-context, storage, ingestion, and retrieval budgets vary. Full-history and expensive extraction strategies remain visible here rather than being silently excluded.

Track separately: ingestion tokens and compute; indexing/storage bytes; model calls; retrieval tokens; answer tokens; wall-clock time; p50/p95 retrieval latency; system memory; CPU/GPU consumption when observable; energy/API cost as measured, estimated, or unavailable. Do not equate a whitespace word count with billed/model tokens or a zero placeholder with a measured zero.

## 7. Dataset construction and anti-bias controls

Prepare an independent **scenario/episode-level holdout**. Histories and their templates, entities, source documents, and paraphrase families must not overlap between development, pilot, and confirmatory partitions. Repeated questions from one history count as correlated observations within one independent cluster.

The primary confirmatory set should be balanced across these preregistered families:

- **Factual and long-horizon recall:** old observations after many distractors and multiple sessions.
- **Temporal, supersession, and late arrival:** current-versus-past state, effective time versus recorded time, reversals and corrections.
- **Relational and cross-frame reasoning:** multihop facts, alias resolution, cross-context joins, evidence provenance.
- **Conflict, uncertainty, and adversarial distractors:** incompatible sources, absence of evidence, valid abstention, misleading near matches.

Include tasks whose answer depends on memory and **negative controls** where it does not. Include examples in which a basic vector retriever should excel, examples favoring a temporal graph, and examples with irrelevant or redundant structure. Difficulty and distractor load should vary across low, medium, and high levels independently of which system is being evaluated.

Create gold answers and permissible evidence paths before methods are scored. Where generated scenarios are used, sample independent entities and values, vary the order of candidates, avoid fixed color labels, remove `supports=<answer>` tags, and ensure the correct response is not evident from prompt templates. A held-out-quality audit must flag leakage, ambiguous gold, duplicate histories, unusable tasks, and accidental method-specific advantages **without inspecting CCM's comparative scores**. Document all exclusions before unsealing outcomes.

Externally sourced evaluation should be fixed before confirmatory execution. Prefer at least one of **LongMemEval** (ICLR 2025), **MemoryAgentBench** (ICLR 2026), or **LongMemEval-V2** (2026) and, if feasible, one interactive memory workload such as **MemoryArena**. Record exact upstream revision, subset selection, license, grouping unit, and evaluator. A public benchmark may be contaminated by model pretraining; report it as external replication, not as hidden ground truth. Do not train or tune on its test labels.

## 8. End-to-end execution sequence and gates

**Phase 0. Audit and freeze source scope.** Snapshot original `main`, manuscript, v0.1 protocol and code. Record exact SHA, repo visibility, licenses, and known defects. Create a v0.2 protocol branch; no historical files rewritten. **Evidence:** audit markdown, diff, manifest. **Gate:** scope approved and historical registration preserved.

**Phase 1. Implement and verify correctness.** Repair leakage, durability, baselines, ablations, true tokenizer accounting, data schemas, scoring, and run manifests. Run property tests, fault injection, temporal edge cases, restart/cross-session checks, and independent metric fixture tests. **Evidence:** local test logs, coverage/results, failure cases, code SHA. **Gate:** all critical tests pass; failure to repair blocks empirical claims.

**Phase 2. Pilot without confirmatory peeking.** Run on distinct development/pilot histories. Calibrate all methods using a symmetric, declared search budget; test scoring reliability and estimate paired effect variance, failure modes, and cost. A pilot is allowed to inform configuration and sample-size planning but may not enter confirmatory estimates. **Evidence:** pilot dataset manifest, tuning ledger, pilot-only raw data, power-simulation output. **Gate:** measurement and comparator fidelity qualified.

**Phase 3. Freeze confirmatory plan.** Publish `ccm-empirical-v0.2.0` with the exact hypotheses, primary endpoint, baseline selection rule and selected comparator, model hashes, prompt hashes, dataset generation/holdout commitments, inclusion criteria, primary token/resource budget, sample size, analysis code, and planned comparisons. Seal or independently hash the holdout inputs and gold; the evaluating agent must be unable to inspect gold while executing methods. **Evidence:** immutable registration commit/tag, checksums. **Gate:** no changes without an explicit protocol amendment.

**Phase 4. Execute confirmatory runs.** Randomize or counterbalance condition execution order at the independent history level to reduce runtime drift and cache effects. Restore fresh memory state for each condition/history; ingest the same chronologically valid history; persist and restart; issue the same queries; record final structured responses. Capture exceptions and timeouts as predeclared outcomes. Do not stop because scores look favorable or unfavorable. **Evidence:** immutable JSONL, logs, manifests, hashes, resume receipts. **Gate:** planned sample accounting complete or limitations explicitly logged.

**Phase 5. Blind scoring and statistical analysis.** Validate record completeness and hashes, score under anonymized condition IDs, audit a stratified sample of judgments independently, and run the frozen analysis code once on the confirmatory set. Save all comparisons including unfavorable results. **Evidence:** scoring audit, raw and processed output, confidence intervals, effect sizes, corrected tests, figures. **Gate:** no selective reporting or silent missing-data removal.

**Phase 6. External generalization.** Run the locked systems on preregistered public benchmark revision(s), preserving official scoring. Clearly separate from Phase 4 and do not alter the primary conclusion to match external results. **Evidence:** dataset sources, licenses, run manifests, native benchmark outputs. **Gate:** any unavailable benchmark is reported as not run, with reason.

**Phase 7. Independent reproduction and publication.** Re-run at least one full subset from a clean checkout, regenerate paper tables/figures directly from machine-readable outputs, audit manuscript claims against the analysis, and tag the evidence release. **Evidence:** clean-run receipt, paper PDF, claim-to-evidence matrix, release assets and checksums. **Gate:** research claims cannot exceed tested support.

**Never use a rerun to replace an unfavorable valid result.** A genuine software bug found after unsealing requires a documented amendment, preservation of the original run, repair tests, and separately identified new execution. Both outputs remain traceable.

## 9. Statistical analysis and error control

**Unit of independence:** a scenario/history or source task family, not each query and not each decoding seed. Pair each history across systems. Apply stratified, **cluster-level paired bootstrap** confidence intervals over histories, preserving the predeclared family weighting. Use a paired permutation or appropriate cluster-aware regression sensitivity analysis. Repeated seeds quantify stochastic variability and remain nested within histories.

**Pilot and power:** choose confirmatory sample size *before outcome access* with reproducible Monte Carlo power simulations using pilot discordance/correlation estimates. Target at least **80% power**, preferably **90%**, for a 5-percentage-point primary improvement under a two-sided 0.05 test. Publish assumptions and sensitivity curves. Three seeds times ten questions per class are **not** automatically sufficient; do not inflate N by counting repeated questions within one history as independent. If the resources cannot support an adequately powered experiment, mark the confirmatory effect **underpowered/inconclusive** and publish estimates transparently.

**Primary decision rule:** report the raw paired GRA difference in percentage points and its cluster-aware 95% CI; test the single frozen primary comparator at two-sided alpha 0.05. Classify:

- **Evidence of benefit:** lower 95% CI bound above zero *and* point estimate at least +5 percentage points.
- **Evidence of harm:** upper 95% CI bound below zero *and* point estimate at most -5 points.
- **Practical equivalence:** only if a prospectively powered equivalence test places the appropriate 90% CI fully within -5 to +5 points.
- **Inconclusive / smaller effect:** everything else, including statistically detectable effects under 5 points, inconclusive intervals, and insufficient sample size. Report the detailed estimate instead of obscuring it behind the label.

The benefit label does not establish that the true effect exceeds five points when its confidence interval crosses +5. State that distinction explicitly. Do not interpret no significance as no effect. If the CI excludes an improvement of +5 points, it can support a narrower statement that a practically important positive effect is unlikely under the study conditions, even if strict equivalence is not shown.

Secondary confirmatory comparisons use a frozen family of tests with **Holm adjustment** or predeclared gatekeeping. Exploratory effects are shown with unadjusted descriptive intervals but no confirmatory success language. Report within-family differences, model-condition interactions, worst-stratum regressions, and the full resource-quality Pareto frontier. Aggregate results must not conceal dramatic degradation in temporal correctness or unsupported-memory behavior.

The scoring audit must evaluate inter-rater agreement for any manual judgments and adjudicate disagreements using a rule defined before viewing condition identity. Independent metric unit tests must verify all denominators, missing-value handling, precision/recall, source sufficiency, abstention, and cluster bootstrap behavior.

## 10. Fault, safety, and negative-control battery

Include both assay-positive controls (a plainly answerable historical fact, and an oracle-retrieval reader ceiling) and assay-negative controls (no memory, unanswerable history). A broken positive control invalidates a performance result even if other metrics look plausible.

In addition to normal evaluation, inject: no relevant memories; irrelevant but semantically similar distractors; contradictory sources; trusted versus untrusted source records; late events; out-of-order writes; deleted/retracted current state; identity aliases; duplicate events; corrupt record/checksum; crash during update; restored session; low token budget; missing tool; fake citation IDs; prompt-injection text inside an observation; cross-history retrieval attempts.

Expected outcomes are specified in advance. For example, unanswerable questions should abstain when required, invalid source IDs should never be credited, and a prompt-injection payload stored as memory must not become an agent instruction. Software correctness failures are reported separately from statistical memory-performance failures.

Use two-sided error scrutiny: **false positive** safeguards include held-out data, strong baselines, no label leakage, frozen tests, multiple-comparison control, blinding, and accounting for costs; **false negative** safeguards include realistic tasks, adequate power, properly tuned comparators and CCM, multiple task families, honest handling of model/tool failures, and recognition of inconclusive estimates.

## 11. Evidence structure and GitHub publication contract

Commit source, configs, manifests, and *public-safe* evidence under a documented immutable code revision. Preferred structure:

```text
preregistration/ccm-v0.2.0/
  PROTOCOL.md
  hypotheses.yaml
  metrics.yaml
  comparisons.yaml
  sample_size_plan.json
  dataset_manifest.json
  freeze.json
experiments/ccm-v0.2.0/
  configs/
  datasets/
  adapters/
  runners/
  grading/
tests/
  contracts/
  adversarial/
  temporal/
  ablations/
  measurement/
evidence/ccm-v0.2.0/
  preflight.json
  validation/
  pilot/
  confirmatory/
    manifests/
    raw/
    scored/
    analysis/
  external/
  reproducibility/
  CLAIM_EVIDENCE_MATRIX.md
  EXECUTION_LEDGER.md
```

Each run manifest must include: exact source SHA, protocol SHA, UTC timestamp, host/OS/hardware, model id and immutable revision, tokenizer version, runtime/quantization, prompts and prompt hashes, dataset and answer-key hashes, scenario/group ID, random seeds, condition, config hash, memory index revision, invocation and resource counts, exit status, paths and SHA-256 checksums, and any deviation ID. Keep credentials and private data out of Git. For large artifacts use GitHub release assets or a content-addressed archive with a checksum and manifest. Store artifact pointers in the repository; do not commit huge opaque archives that prevent review.

Because paid hosted CI may be unavailable, **local manual CI is the authoritative execution path**. Every command must yield a nonfabricated machine-readable receipt with exact command, exit code, start/stop time, environment, log path, test count, source SHA, and artifact digests. Commit these receipts and the validation logs to the repo. GitHub Actions, when available, may perform lightweight verification but are not necessary to satisfy this protocol. Independent clean-checkout reproduction is still mandatory.

Required outputs: test report; pilot/tuning and power report; immutable preregistration; complete run accounting with failures; per-history anonymized responses; score audit; paired comparisons and uncertainty; negative-result and deviation ledger; resource-quality plots; external benchmark report; reproducible analysis script; generated paper tables; final PDF; and a GitHub release whose tag resolves to the evaluated code.

## 12. Execution commands and stop rules

The following are **interfaces to implement**, not commands claimed to exist today:

```bash
./scripts/ccm_preflight
./scripts/ccm_verify --all --evidence-dir evidence/ccm-v0.2.0/validation
./scripts/ccm_pilot --config experiments/ccm-v0.2.0/configs/pilot.yaml
./scripts/ccm_power --pilot evidence/ccm-v0.2.0/pilot
./scripts/ccm_freeze --protocol preregistration/ccm-v0.2.0/PROTOCOL.md
./scripts/ccm_run --config experiments/ccm-v0.2.0/configs/confirmatory.yaml
./scripts/ccm_grade --blind --config experiments/ccm-v0.2.0/configs/scoring.yaml
./scripts/ccm_analyze --frozen preregistration/ccm-v0.2.0/freeze.json
./scripts/ccm_reproduce --clean-checkout
./scripts/ccm_audit_evidence
```

**Stop before confirmatory execution** if there is label leakage, unverifiable baseline fidelity, invalid sample independence, material untested source changes, invalid manifests, or unversioned gold labels. If a real local or approved hosted model cannot be run, finish the software-validation stage, record `EMPIRICAL_BLOCKED_ENVIRONMENT`, and do **not** relabel ToyModel scores as real-model findings. A limited powered-down run may be published as exploratory only.

## 13. Acceptance criteria and publication decision

A credible completed protocol requires (1) frozen prospective registration; (2) no ground-truth exposure; (3) real, independently implemented baselines; (4) durable CCM across sessions; (5) verified distinct ablations; (6) matched model/input/budget comparisons; (7) adequately powered independent-history sample or transparent underpowered designation; (8) full outcome accounting; (9) honest statistical categories; (10) at least one external replication attempt; (11) clean-checkout reproducibility; and (12) an auditable GitHub evidence release.

The final paper must separate **implemented and tested**, **measured within this environment**, **not demonstrated**, and **future work**. Null, mixed, and negative findings are first-class results. A scientifically credible negative result is preferable to a favorable result from a biased protocol.

## 14. Research references and public benchmark options

- LongMemEval (ICLR 2025), original study and task format: https://github.com/xiaowu0162/LongMemEval
- LongMemEval-V2 (2026), agentic long-term memory: https://github.com/xiaowu0162/LongMemEval-V2
- MemoryAgentBench (ICLR 2026), incremental multi-turn memory: https://github.com/HUST-AI-HYZ/MemoryAgentBench
- MemoryArena (2026), interdependent multi-session agentic tasks: https://github.com/ZexueHe/MemoryArena
- OSF, prospective registration and amendments: https://help.osf.io/article/330-welcome-to-registrations
- NeurIPS reproducibility checklist: https://neurips.cc/public/guides/PaperChecklist

These references guide benchmark and disclosure choices. Their existence does not substitute for independent verification of licenses, data integrity, score comparability, or the suitability of any specific subset for CCM.
