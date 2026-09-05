# Cortical-Column Memory

**Cortical-Column Memory (CCM)** is a model-agnostic, agent-internal memory architecture inspired by selected computational principles associated with Thousand Brains Theory. CCM organizes persistent memory as multiple bounded local models that retain structured observations, provenance, temporal history, reference-frame context, evidence-bearing hypotheses, and reconciled state.

**Release:** `v0.1.0` — architecture and preregistered evaluation protocol
**Status:** Preprint — not peer reviewed; registered campaign pending
**Canonical repository:** <https://github.com/jmsbooth/cortical-column-memory>

## Research question

Does maintaining structured modular world-state memory improve relevant recall, temporal consistency, relational reconstruction, provenance, and downstream agent performance compared with transcript, summary, vector, structured, or knowledge-graph memory under matched task and resource conditions?

Model-scale interaction and multi-agent composition are secondary research dimensions. The deterministic toy adapter validates contracts and software behavior; it is not evidence of language-model capability or empirical superiority.

## What CCM is

An agent may contain one CCM instance composed of multiple bounded columns:

```text
Environment / user / tools
            |
            v
+-----------------------------+
|            Agent            |
|  reasoning model, tools,    |
|  planning, working context  |
|             |               |
|             v               |
|  +-----------------------+  |
|  |          CCM          |  |
|  | Column A  Column B    |  |
|  | Column C  ...         |  |
|  | local models          |  |
|  | reference frames      |  |
|  | history and state     |  |
|  | recall and reconcile  |  |
|  +-----------------------+  |
+-----------------------------+
```

The agent-facing interface is intentionally bounded:

```text
recall(query, current_context, budget)
        |
        v
local models -> reconciliation -> provenance-bearing context -> model
```

A multi-agent deployment is a separate composition layer. Each agent may independently contain CCM; CCM does not prescribe the orchestrator, transport, or coordination topology.

## What CCM is not

- not a biological cortex simulation or a claim of equivalence between software columns and biological cortical columns;
- not the Thousand Brains Project or Monty;
- not an LLM, model provider, or agent framework;
- not inherently a multi-agent framework;
- not dependent on TPAA;
- not a requirement that every recall be resolved by quorum voting.

## Architecture

The implementation separates immutable historical observations from interpreted current state. It includes typed relations, hypotheses, predictions, explicit reference frames, bounded recall, context assembly, optional active evidence, and reconciliation outcomes including agreement, complementary state, contradiction, unresolved disagreement, and unknown.

The default conceptual mode is shared-model: columns may call the same parent-agent model while maintaining distinct state. Heterogeneous model adapters are supported as a provider-neutral interface, but no hosted credentials or provider are required.

## Quick start

```bash
./scripts/setup
./scripts/run_smoke
./scripts/analyze results/raw/ccm-smoke-v0.1.0.jsonl
python3 -m unittest discover -s tests -t . -v
./scripts/build_paper
```

The smoke run is deterministic at the task/decision level and is labelled software validation, not a registered empirical result.

## Repository structure

```text
ccm/                 contracts, memory, frames, columns, recall, adapters
experiments/         memory-first baselines, task worlds, runners
evaluation/          memory metrics, resource accounting, statistics
preregistration/     protocol, hypotheses, metrics, registered config
paper/               LaTeX source, figures/tables, bibliography, PDF
tests/               unit, integration, invariant, regression, smoke tests
docs/                architecture, memory model, reference frames, reproduction
results/              manifest-backed smoke artifacts only
```

## Research status

`v0.1.0` publishes the architecture, reference implementation, tests, synthetic validation environments, machine-readable manifests, and preregistered protocol before the full campaign. No checked-in smoke measurement is presented as evidence for a scientific claim.

## Paper

- [Compiled paper](paper/build/main.pdf)
- [LaTeX source](paper/main.tex)
- [Preregistration](preregistration/protocol.md)
- [Release checklist](RELEASE_CHECKLIST.md)

## Reproducing tests and experiments

See [docs/reproduction.md](docs/reproduction.md) for the clean-checkout sequence and [docs/experiment-guide.md](docs/experiment-guide.md) for the primary memory baselines, secondary composition baselines, task classes, metrics, and statistical controls.

Every run records configuration and task hashes, model/task versions, seed, hardware metadata, Git commit, resource fields, structured traces, and generated output paths. Unavailable hardware or energy measurements are recorded as unavailable rather than fabricated.

## Citation

```bibtex
@software{booth_ccm_2026,
  author  = {James Booth},
  title   = {Cortical-Column Memory: A Thousand-Brains-Inspired Architecture for Structured Agent Memory},
  version = {0.1.0},
  year    = {2026},
  url     = {https://github.com/jmsbooth/cortical-column-memory}
}
```

See [`CITATION.cff`](CITATION.cff). Please preserve the provenance and license of any external model, dataset, or generated artifact used in future experiments.

## License

Code is released under the [MIT License](LICENSE). The paper is released under [CC BY 4.0](paper/LICENSE).
