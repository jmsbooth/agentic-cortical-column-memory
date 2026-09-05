# Reference frames

A reference frame answers: **relative to what structured context does this observation have meaning?**

```text
F = (frame_id, kind, origin, current_state, transitions, observations_by_state)
```

Frames are not necessarily spatial. CCM supports the following conceptual classes:

- object-relative — locations on or around an object;
- actor-relative — state associated with a person, service, or agent;
- process-relative — stages in a process or workflow;
- temporal — validity intervals and historical queries;
- spatial — physical or simulated locations;
- relational — a connected state neighborhood;
- workflow/state-machine — valid transitions and actions;
- domain-specific ontology frame — valid entity/predicate structures supplied by an external schema.

An ontology defines which entities and relationships are valid. CCM stores observed instances and updates them over time. For example:

```text
Ontology: Session accesses Resource.
CCM:      Session S19 accessed Resource R4 at 14:32 using Token T7.
```

The runtime validates transitions and frame/location identity. It does not claim that software state spaces reproduce biological reference frames.
