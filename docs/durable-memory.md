# CCM-EMP-002 Phase 1B: Durable agent memory

**Status:** Experimental implementation, not an empirical memory-quality result. This increment does not freeze the v0.2.0 preregistration and does not make performance claims.

CCM separates the lifetime of an agent's reasoning call from the lifetime of its persistent memory. `SQLiteMemoryStore` stores immutable observations in SQLite, with records scoped to an `(agent_id, column_id)` pair. The store exposes `write`, `write_many`, `get`, `retrieve`, `historical`, `current`, `supersede`, `all`, `recall`, `trace`, `snapshot_digest`, and `stats` operations. The in-memory store remains an explicit software-control backend.

## Opening and closing

```python
from ccm.memory.durable import SQLiteMemoryStore

with SQLiteMemoryStore("./var/ccm.sqlite3", agent_id="agent-1", column_id="identity") as memory:
    # pass memory to the agent's injected memory_factory or use it directly
    history = memory.historical("identity-frame", at_time="2026-01-01T00:00:00Z")
```

The SQLite file survives process restarts. `PRAGMA user_version` fixes schema version 1; newer or incompatible schema versions are rejected rather than silently downgraded. The backend uses WAL mode, foreign keys, full synchronous writes, atomic observation batches, and atomic supersession links. Each opened store performs a SQLite quick-check and foreign-key/schema checks. All reads and writes are constrained by the local agent and column namespace.

`recorded_at` in the observation, if explicitly supplied by a trusted importer, is treated as the ingestion time for bitemporal queries. Otherwise ingestion time is captured separately by the store. An observation is never modified in place, including for corrections. A replacement must be separately appended and linked with `supersede(old_id, new_id, effective_at=...)`.

## Historical and as-known-at semantics

- `historical(frame_id, at_time=T)` returns **all temporally anchored** observations valid in world time T, including contradictions and late-entered evidence. A valid-from timestamp, or at least an observation timestamp, must establish that the fact was available no later than T. Undated entries remain in raw history but cannot assert truth at an arbitrary historical time.
- `historical(frame_id, at_time=T, known_at=K)` further limits results to observations recorded by system time K. A late-arriving observation is not visible in an earlier as-known-at view.
- `current(frame_id, at_time=T, known_at=K)` derives the unsuperseded view at world time T, as known by system time K. A supersession recorded after K has no effect in that earlier knowledge view.
- `current(frame_id)` derives the present interpretation, including undated observations as current evidence when not explicitly expired. Records that conflict without an explicit supersession remain visible rather than silently choosing the newest record.
- If a supersession has no trustworthy effective time, it may suppress the old record in the present view but does not rewrite point-in-time historical queries. Ambiguous history remains visible.

Timestamps must be timezone-aware ISO 8601/RFC3339 strings. Naive or malformed strings, reversed validity intervals, identity conflicts, cross-namespace references, invalid migrations, and supersession cycles fail closed.

## Evaluator isolation

`write_visible_case` accepts **only** a `ModelVisibleCase` from Phase 1A. It revalidates the allowlisted case at the boundary and atomically translates its visible observations. It never receives an evaluator record, gold answer, answer-key order, or grader metadata. Its stored `validation_state` remains `unvalidated` until separate evidence validation occurs. The generic `write(Observation)` method is an explicitly trusted environment/importer interface; it must never be exposed directly to untrusted model output or to the evaluator.

## Operational boundaries

The SQLite backend is not encryption-at-rest, multi-user authorization, distributed replication, globally consistent memory, or a substitute for database backups. The SHA-256 payload digest detects accidental/casual record alteration but is not an authenticated tamper-proof ledger. Per-agent/column scope is an application contract, not a replacement for OS-level filesystem permissions. Results from these tests demonstrate storage contracts, not improvements over RAG, graph memory, or another baseline.

The engine remains an agent-level runtime; the memory factory is injected rather than requiring each CCM column to become a separate autonomous agent. Multiple agent workers can instantiate independent stores. A filesystem backup or WAL-aware backup should be part of an eventual production deployment; it is outside Phase 1B's local reference scope.
