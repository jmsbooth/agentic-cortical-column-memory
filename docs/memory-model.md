# CCM memory model

CCM separates what was observed from what is currently inferred.

| Object | Meaning | Mutability |
| --- | --- | --- |
| `Observation` | Externally acquired fact or state with source and provenance | immutable |
| `Relation` | Typed subject/predicate/object relationship | append-only |
| `State` | Current interpretation derived from observations within a frame | replaceable interpretation |
| `Hypothesis` | Candidate explanation or state not yet confirmed | derived |
| `Transition` | Validated or hypothesized state change | explicit contract |
| `Prediction` | Expected observation under a hypothesis | derived |

## Temporal semantics

Observations may record observed time and recorded time separately, plus `valid_from`, `valid_to`, and `superseded_by`. A late-arriving observation is appended with its own sequence and timestamps. Historical queries use validity intervals; current-state queries select the latest non-superseded interpretation without deleting history.

## Recall API

```python
from ccm.recall import RecallQuery, assemble_context

context = store.recall(
    RecallQuery(
        query="which credential accessed resource R4?",
        frame_id="frame:incident",
        at_time="2026-03-04T14:32:00Z",
        max_items=8,
        max_context_tokens=256,
    )
)
prompt_context = assemble_context(context, max_tokens=256)
```

`MemoryContext` contains selected observations, current state, supporting IDs, conflict groups, hypotheses, provenance, confidence, and a measured context-token count. The implementation uses deterministic lexical scoring for the toy adapter; a future adapter may use an index or learned retriever while retaining the same provenance contract.

## Context assembly

Raw internal memory is not automatically inserted into a model prompt:

```text
agent query + current context + budget
                 |
                 v
              CCM recall
                 |
                 v
      local state and supporting observations
                 |
                 v
           reconciliation
                 |
                 v
 bounded provenance-bearing memory context
                 |
                 v
           reasoning model
```

The assembly boundary is where context tokens, relevant-evidence coverage, provenance coverage, unresolved conflicts, and retrieval latency are measured.
