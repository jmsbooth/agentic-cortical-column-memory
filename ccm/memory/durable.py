"""CCM-EMP-002 SQLite memory backend, scoped to one agent and one column.

Uses only the Python standard library.  Historical events are immutable; state
is a derived view.  Transactions protect observation and supersession writes.
The evaluator's gold fields are not part of this persistence API.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter_ns
from typing import TYPE_CHECKING, Iterable

from ccm.memory.store import MemoryConflict, MemoryOperation
from ccm.schemas.models import Observation

if TYPE_CHECKING:
    from ccm.empirical.contracts import ModelVisibleCase
    from ccm.recall.core import MemoryContext, RecallQuery


_SCHEMA_VERSION = 1


def _instant(value: str | None) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise MemoryConflict("time must be a nonempty RFC3339 string")
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise MemoryConflict(f"invalid timestamp: {value!r}") from error
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise MemoryConflict("naive timestamps are not admissible")
    return instant.astimezone(timezone.utc)


def _iso(value: str | None) -> str | None:
    instant = _instant(value)
    return instant.isoformat(timespec="microseconds") if instant is not None else None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _valid_at(observation: Observation, when: datetime) -> bool:
    start, end = _instant(observation.valid_from), _instant(observation.valid_to)
    return (start is None or start <= when) and (end is None or when < end)


def _validate(observation: Observation) -> None:
    if type(observation) is not Observation:
        raise MemoryConflict("memory writes require validated Observation objects")
    # Revalidate even a frozen dataclass: object.__setattr__ or unsafe import
    # paths can bypass its original constructor after initialization.
    try:
        Observation(**observation.to_dict())
    except (ValueError, TypeError) as error:
        raise MemoryConflict("observation fails canonical schema validation") from error
    if not observation.object_id or not observation.frame_id or not observation.location:
        raise MemoryConflict("observation must have stable identity, frame and location")
    if not observation.source or not observation.provenance:
        raise MemoryConflict("observation source and provenance required")
    if observation.kind == "external" and observation.source.startswith("model:"):
        raise MemoryConflict("model-generated text is not an external observation")
    if observation.superseded_by:
        raise MemoryConflict("supersession must use the transactional supersede operation")
    for field in ("observed_at", "recorded_at", "valid_from", "valid_to"):
        _instant(getattr(observation, field))
    start, end = _instant(observation.valid_from), _instant(observation.valid_to)
    if start is not None and end is not None and end <= start:
        raise MemoryConflict("validity interval must have positive duration")


def _decode(payload: str) -> Observation:
    obj = json.loads(payload)
    if type(obj) is not dict:
        raise MemoryConflict("invalid stored observation")
    obj["relations"] = tuple(obj.get("relations") or ())
    if obj.get("embedding") is not None:
        obj["embedding"] = tuple(obj["embedding"])
    return Observation(**obj)


@dataclass(frozen=True)
class StorageStats:
    write_count: int
    read_count: int
    write_wall_ns: int
    read_wall_ns: int
    storage_bytes: int


class SQLiteMemoryStore:
    """Durable, agent/column-local append-only memory with explicit temporal state.

    A database file can contain several agents/columns, but every instance is
    locked to one pair.  The database never provides a global, unrestricted
    read API.  The caller must explicitly close each instance.
    """

    def __init__(self, database: str | Path, *, agent_id: str, column_id: str = "shared") -> None:
        if not agent_id or not column_id or not agent_id.strip() or not column_id.strip():
            raise MemoryConflict("agent and column namespaces are required")
        self.agent_id, self.column_id = agent_id, column_id
        self.database = Path(database)
        if self.database != Path(":memory:"):
            self.database.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(database), timeout=15, isolation_level=None)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA busy_timeout = 15000")
        if self.database != Path(":memory:"):
            self._conn.execute("PRAGMA journal_mode = WAL")
            self._conn.execute("PRAGMA synchronous = FULL")
        self._closed = False
        self._writes = self._reads = self._write_ns = self._read_ns = 0
        self._initialize()

    def _initialize(self) -> None:
        version = int(self._conn.execute("PRAGMA user_version").fetchone()[0])
        if version not in (0, _SCHEMA_VERSION):
            raise MemoryConflict(f"unsupported schema version: {version}")
        if version == 0:
            ddl = (
                """CREATE TABLE IF NOT EXISTS observations (
                    agent_id TEXT NOT NULL, column_id TEXT NOT NULL,
                    object_id TEXT NOT NULL, frame_id TEXT NOT NULL,
                    location TEXT NOT NULL, sequence INTEGER NOT NULL,
                    ingested_at TEXT NOT NULL, payload TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    PRIMARY KEY(agent_id, column_id, object_id)
                )""",
                """CREATE INDEX IF NOT EXISTS by_frame ON observations
                    (agent_id, column_id, frame_id, location, sequence)""",
                """CREATE TABLE IF NOT EXISTS supersessions (
                    agent_id TEXT NOT NULL, column_id TEXT NOT NULL,
                    old_id TEXT NOT NULL, new_id TEXT NOT NULL,
                    effective_at TEXT, recorded_at TEXT NOT NULL,
                    PRIMARY KEY(agent_id, column_id, old_id),
                    FOREIGN KEY(agent_id,column_id,old_id) REFERENCES observations(agent_id,column_id,object_id),
                    FOREIGN KEY(agent_id,column_id,new_id) REFERENCES observations(agent_id,column_id,object_id)
                )""",
                """CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL, column_id TEXT NOT NULL,
                    operation TEXT NOT NULL, object_id TEXT NOT NULL, sequence INTEGER NOT NULL
                )""",
                "PRAGMA user_version = 1",
            )
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                for statement in ddl:
                    self._conn.execute(statement)
                self._conn.execute("COMMIT")
            except Exception:
                if self._conn.in_transaction:
                    self._conn.execute("ROLLBACK")
                raise
        required = {"observations", "supersessions", "operations"}
        present = {
            row[0] for row in self._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if not required.issubset(present):
            raise MemoryConflict("expected SQLite schema tables are missing")
        required_columns = {
            "observations": {"agent_id", "column_id", "object_id", "payload", "payload_sha256", "ingested_at"},
            "supersessions": {"agent_id", "column_id", "old_id", "new_id", "effective_at", "recorded_at"},
            "operations": {"id", "agent_id", "column_id", "operation", "object_id", "sequence"},
        }
        for table, columns in required_columns.items():
            actual = {row[1] for row in self._conn.execute(f"PRAGMA table_info({table})")}
            if not columns.issubset(actual):
                raise MemoryConflict(f"SQLite schema columns missing: {table}")
        result = self._conn.execute("PRAGMA quick_check").fetchone()[0]
        if result != "ok" or self._conn.execute("PRAGMA foreign_key_check").fetchone():
            raise MemoryConflict("SQLite integrity checks failed")

    def _check_open(self) -> None:
        if self._closed:
            raise MemoryConflict("closed memory store")

    def close(self) -> None:
        if not self._closed:
            self._conn.close()
            self._closed = True

    def __enter__(self) -> "SQLiteMemoryStore":
        self._check_open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _rows(self, *, frame_id: str | None = None, location: str | None = None, known_at: str | None = None) -> tuple[Observation, ...]:
        self._check_open()
        sql = "SELECT payload,payload_sha256 FROM observations WHERE agent_id=? AND column_id=?"
        params: list[object] = [self.agent_id, self.column_id]
        if frame_id is not None:
            sql += " AND frame_id=?"
            params.append(frame_id)
        if location is not None:
            sql += " AND location=?"
            params.append(location)
        if known_at is not None:
            sql += " AND ingested_at<=?"
            params.append(_iso(known_at))
        sql += " ORDER BY sequence, object_id"
        decoded = []
        for payload,digest in self._conn.execute(sql, params).fetchall():
            if hashlib.sha256(payload.encode("utf-8")).hexdigest() != digest:
                raise MemoryConflict("stored observation content has changed")
            decoded.append(_decode(payload))
        return tuple(decoded)

    def _insert(self, observation: Observation) -> None:
        _validate(observation)
        payload = json.dumps(observation.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self._conn.execute(
            "INSERT INTO observations(agent_id,column_id,object_id,frame_id,location,sequence,ingested_at,payload,payload_sha256) VALUES (?,?,?,?,?,?,?,?,?)",
            (self.agent_id, self.column_id, observation.object_id, observation.frame_id,
             observation.location, observation.sequence, _iso(observation.recorded_at) or _now(), payload, digest),
        )
        self._conn.execute(
            "INSERT INTO operations(agent_id,column_id,operation,object_id,sequence) VALUES (?,?,?,?,?)",
            (self.agent_id,self.column_id,"write",observation.object_id,observation.sequence),
        )

    def write_many(self, observations: Iterable[Observation]) -> None:
        self._check_open()
        start = perf_counter_ns()
        observations = tuple(observations)
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            for observation in observations:
                self._insert(observation)
            self._conn.execute("COMMIT")
        except Exception as error:
            self._conn.execute("ROLLBACK")
            if isinstance(error, sqlite3.IntegrityError):
                raise MemoryConflict("duplicate memory identity or invalid reference") from error
            raise
        self._writes += len(observations)
        self._write_ns += perf_counter_ns() - start

    def write(self, observation: Observation) -> None:
        self.write_many((observation,))

    def write_visible_case(self, case: "ModelVisibleCase") -> None:
        """Only the Phase 1A allowlisted input type can cross this ingress path."""
        from ccm.empirical.contracts import BoundaryViolation, ModelVisibleCase
        from ccm.empirical.operations import plan_memory_writes
        if type(case) is not ModelVisibleCase:
            raise BoundaryViolation("durable memory ingest requires ModelVisibleCase")
        # Revalidate the exact allowlisted representation at ingress, including
        # any dataclass that was mutated after its original construction.
        case = ModelVisibleCase.from_dict(case.to_dict())
        instructions = plan_memory_writes(case)
        observations = tuple(
            Observation(
                object_id=item.observation_id,
                content=item.content,
                frame_id=item.frame_id,
                location=item.location,
                source=item.source_id,
                sequence=index,
                confidence=1.0,
                provenance=f"visible-case:{case.case_id}:{item.source_id}",
                observed_at=item.observed_at,
                validation_state="unvalidated",
            )
            for index, item in enumerate(instructions)
        )
        self.write_many(observations)

    def get(self, object_id: str) -> Observation:
        self._check_open()
        match = self._conn.execute(
            "SELECT payload,payload_sha256 FROM observations WHERE agent_id=? AND column_id=? AND object_id=?",
            (self.agent_id,self.column_id,object_id),
        ).fetchone()
        if match is None:
            raise KeyError(object_id)
        payload,digest = match
        if hashlib.sha256(payload.encode("utf-8")).hexdigest() != digest:
            raise MemoryConflict("stored observation content has changed")
        return _decode(payload)

    def retrieve(self, frame_id: str, location: str | None = None, limit: int | None = None) -> tuple[Observation, ...]:
        start = perf_counter_ns()
        values = self._rows(frame_id=frame_id, location=location)
        if limit is not None:
            if limit < 0:
                raise MemoryConflict("negative recall limit")
            values = values[:limit]
        self._reads += 1
        self._read_ns += perf_counter_ns() - start
        return values

    def historical(
        self, frame_id: str, *, location: str | None = None,
        at_time: str | None = None, known_at: str | None = None, limit: int | None = None,
    ) -> tuple[Observation, ...]:
        when = _instant(at_time)
        values = self._rows(frame_id=frame_id, location=location, known_at=known_at)
        if when is not None:
            values = tuple(item for item in values if _valid_at(item, when))
        return values[:limit] if limit is not None else values

    def supersede(self, observation_id: str, replacement_id: str, *, effective_at: str | None = None, recorded_at: str | None = None) -> None:
        self._check_open()
        if observation_id == replacement_id:
            raise MemoryConflict("self-supersession not allowed")
        old,new = self.get(observation_id),self.get(replacement_id)
        if (old.frame_id,old.location)!=(new.frame_id,new.location):
            raise MemoryConflict("supersession requires same reference frame and location")
        effective = _instant(effective_at) or _instant(new.valid_from) or _instant(new.observed_at)
        prior = _instant(old.valid_from)
        if effective is not None and prior is not None and effective < prior:
            raise MemoryConflict("supersession predates the original state")
        # Lock before graph validation so concurrent writers cannot create cycles.
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            graph = self.supersession_map()
            node = replacement_id
            seen = {observation_id}
            while node in graph:
                if node in seen:
                    raise MemoryConflict("supersession cycle")
                seen.add(node)
                node = graph[node]
            if node == observation_id:
                raise MemoryConflict("supersession cycle")
            self._conn.execute(
                "INSERT INTO supersessions(agent_id,column_id,old_id,new_id,effective_at,recorded_at) VALUES(?,?,?,?,?,?)",
                (self.agent_id,self.column_id,observation_id,replacement_id,
                 effective.isoformat(timespec="microseconds") if effective else None,_iso(recorded_at) or _now()),
            )
            self._conn.execute(
                "INSERT INTO operations(agent_id,column_id,operation,object_id,sequence) VALUES(?,?,?,?,?)",
                (self.agent_id,self.column_id,"supersede",observation_id,new.sequence),
            )
            self._conn.execute("COMMIT")
        except sqlite3.IntegrityError as error:
            if self._conn.in_transaction:
                self._conn.execute("ROLLBACK")
            raise MemoryConflict("observation already superseded or foreign reference") from error
        except Exception:
            if self._conn.in_transaction:
                self._conn.execute("ROLLBACK")
            raise

    def _supersessions(self, known_at: str | None = None) -> dict[str, tuple[str, str | None, str]]:
        self._check_open()
        return {
            old_id: (new_id, effective_at, recorded_at)
            for old_id,new_id,effective_at,recorded_at in self._conn.execute(
                "SELECT old_id,new_id,effective_at,recorded_at FROM supersessions WHERE agent_id=? AND column_id=?",
                (self.agent_id,self.column_id),
            )
            if known_at is None or _instant(recorded_at) <= _instant(known_at)
        }

    def current(self, frame_id: str, *, location: str | None = None, at_time: str | None = None, known_at: str | None = None) -> tuple[Observation, ...]:
        when = _instant(at_time) if at_time is not None else datetime.now(timezone.utc)
        candidates = self.historical(frame_id, location=location, at_time=when.isoformat(), known_at=known_at)
        links = self._supersessions(known_at)
        result = []
        for obs in candidates:
            link = links.get(obs.object_id)
            if link is not None:
                _,effective_at,_recorded_at = link
                # Undated replacement is unknown for an explicit historical query.
                if at_time is None or (effective_at is not None and _instant(effective_at) <= when):
                    continue
            result.append(obs)
        # Never silently collapse contradictory unsuperseded observations.
        return tuple(result)

    def all(self) -> tuple[Observation, ...]:
        return self._rows()

    def supersession_map(self) -> dict[str, str]:
        return {old:new for old,(new,_,_) in self._supersessions().items()}

    def operations(self) -> tuple[MemoryOperation, ...]:
        self._check_open()
        return tuple(
            MemoryOperation(operation,obj,seq)
            for operation,obj,seq in self._conn.execute(
                "SELECT operation,object_id,sequence FROM operations WHERE agent_id=? AND column_id=? ORDER BY id",
                (self.agent_id,self.column_id),
            )
        )

    def trace(self) -> list[dict[str, object]]:
        return [dict(operation=x.operation, object_id=x.object_id, sequence=x.sequence) for x in self.operations()]

    def recall(self, query: "RecallQuery", *, current_context: str = "", hypotheses: tuple[object, ...] = ()) -> "MemoryContext":
        from ccm.recall.core import recall
        return recall(self, query, current_context=current_context, hypotheses=hypotheses)

    def snapshot_digest(self) -> str:
        payload = {
            "agent_id":self.agent_id,"column_id":self.column_id,
            "observations":[item.to_dict() for item in self.all()],
            "supersessions":sorted((old,new,time,recorded) for old,(new,time,recorded) in self._supersessions().items()),
        }
        return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")).hexdigest()

    def stats(self) -> StorageStats:
        self._check_open()
        nbytes = 0
        if self.database != Path(":memory:"):
            for suffix in ("", "-wal", "-shm"):
                path = Path(str(self.database) + suffix)
                if path.exists():nbytes += path.stat().st_size
        return StorageStats(self._writes,self._reads,self._write_ns,self._read_ns,nbytes)
