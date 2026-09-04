# CCM architecture

## Boundary with the inspiration

CCM uses selected computational ideas associated with the Thousand Brains literature as design prompts. It does not implement biological neurons, cortical layers, grid cells, or a claim about neocortical equivalence. The current TBP/Monty system is a separate sensorimotor learning implementation. HTM is a related algorithmic lineage whose sparse distributed representations and sequence-memory terminology must not be treated as interchangeable with TBT, Monty, or CCM.

## Reference frame

A CCM reference frame is a navigable state space:

```text
Frame = (frame_id, kind, origin, current_state, transitions, observations_by_state)
Transition = (action, source_state, target_state)
```

An object-oriented example maps a camera observation at `handle_left` to an object-local location, applies `rotate_90`, and predicts `handle_top`; a conceptual example maps `claim_unresolved` through `inspect_source_a` to `claim_supported`. `ccm/reference_frames/core.py` rejects transitions from the wrong state or observations from another frame.

## Column and memory contracts

A column is a local model plus state, not a complete agent. It has `observe`, `update_hypotheses`, `propose_action`, `emit_state`, `receive_peer_state`, `vote`, and `commit` operations. A memory object is an immutable `Observation` containing an object ID, content, frame, location, source, sequence, confidence, provenance, validation state, relations, and optional embedding. The implementation does not call ordinary embeddings SDRs.

## Consensus and active evidence

Votes reference hypotheses with frame, location, confidence, evidence IDs, and provenance. Structured consensus requires compatible frame/location/claim keys, quorum, confidence, and a margin over competing groups. A tie or insufficient confidence becomes `unresolved` or `abstained`. The active policy ranks unused actions by expected information gain divided by cost and appends the resulting observation; it does not invent evidence.

## Invariants

1. Every observation has provenance and an explicit source.
2. Model-generated information cannot be stored as an external observation.
3. Every hypothesis names a reference frame and every vote references an existing hypothesis object.
4. Historical observations cannot be mutated or silently overwritten.
5. Conflicting evidence remains in the trace; resolution is not implicit.
6. Run manifests persist configuration/model/task versions, seed, git commit, hardware, and result identity.
7. A system may commit, abstain, or remain unresolved; consensus is never forced.
