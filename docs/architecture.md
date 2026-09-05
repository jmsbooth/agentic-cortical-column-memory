# CCM architecture

## Boundary

CCM is a modular persistent-memory architecture inside an AI agent. A CCM column is not an agent. An agent may contain one CCM instance composed of multiple bounded columns, and multiple agents may independently contain CCM. The outer agent still owns reasoning, planning, tools, instructions, and working context.

```text
Environment / user / tools
            |
            v
Agent: reasoning model + planning + tools + working context
            |
            v
CCM: columns + local models + frames + history + state + recall
            |
            v
bounded, provenance-bearing context for the reasoning model
```

The multi-agent extension is separate:

```text
Orchestrator
  |-- Agent A -- CCM A -- bounded state exchange
  |-- Agent B -- CCM B -- bounded state exchange
  `-- Agent C -- CCM C -- bounded state exchange
```

CCM does not prescribe this topology, a transport, or TPAA. It can be embedded in TPAA or another agent framework as a memory substrate.

## Column contract

A column is a bounded persistent modeling unit responsible for one coherent subset or perspective of world state. It may accept observations, place them in a reference frame, maintain structured state and relations, retain history, track contradictions, derive hypotheses, request evidence, and emit a bounded state representation. It does not need to be a full autonomous agent.

The default mode is shared-model: all columns may call the parent agent's model while maintaining separate state. The provider-neutral `ccm.adapters.ModelAdapter` contract also permits future heterogeneous models.

## Memory and recall

The memory model distinguishes immutable `Observation`, typed `Relation`, interpreted `State`, unconfirmed `Hypothesis`, validated or hypothesized `Transition`, and `Prediction`. Historical observations are never overwritten. Current state is derived separately and may supersede an earlier interpretation while retaining the earlier event.

The agent-facing operation is:

```python
context = memory.recall(
    RecallQuery(query, frame_id, location, at_time, budget),
    current_context=current_context,
    hypotheses=hypotheses,
)
prompt_context = assemble_context(context, max_tokens=budget)
```

The returned context is bounded and includes relevant state, supporting observations, temporal information, provenance, unresolved conflicts, hypotheses, confidence, and candidate evidence gaps.

## Reconciliation

CCM does not define memory recall as voting. Local models are first classified as:

- agreement — compatible state claims;
- complementary — non-overlapping state contributions;
- contradiction — incompatible claims in the same frame/location;
- unresolved — insufficient information to reconcile; or
- unknown — no derived state.

`structured_consensus` remains one optional quorum algorithm for a downstream commit decision. The broader `reconcile_hypotheses` contract is the primary architectural operation.

## Reference frames

A frame is a structured context relative to which an observation has meaning:

```text
Frame = (frame_id, kind, origin, current_state, transitions, observations_by_state)
Transition = (action, source_state, target_state)
```

Supported conceptual classes include object-relative, actor-relative, process-relative, temporal, spatial, relational, workflow/state-machine, and domain-specific ontology frames. See [reference-frames.md](reference-frames.md).

## Incident-investigation example

An incident frame may contain `Actor`, `Session`, `Device`, `Credential`, `Resource`, `Action`, `Time`, and `Authorization context`. CCM can retain the source observation that session `S19` accessed resource `R4` at `14:32` using credential `T7`, then recall only the relevant state and provenance for an agent's next decision. The ontology, if present, defines which entities and predicates are valid; CCM stores the observed instances over time.

## Invariants

1. Observations are immutable and provenance-bearing.
2. Model-generated hypotheses cannot masquerade as external observations.
3. Historical events and current interpreted state are distinct.
4. Temporal validity, supersession, and late-arriving events are explicit.
5. A column cannot silently mutate another column's state.
6. Reconciliation preserves contradiction and unknown outcomes.
7. Recall output is bounded, deterministic for the symbolic adapter, and provenance-linked.
8. Run manifests record versions, configuration, seed, hardware, resources, and Git commit.
