"""Resource accounting with explicit measured/estimated/unavailable fields."""

from __future__ import annotations

import platform
import time
from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass
class ResourceUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    model_invocations: int = 0
    wall_clock_ms: float = 0.0
    cpu_utilization_pct: Optional[float] = None
    gpu_utilization_pct: Optional[float] = None
    peak_memory_mb: Optional[float] = None
    accelerator_seconds: Optional[float] = None
    energy_joules: Optional[float] = None
    api_cost_usd: Optional[float] = None
    communication_bytes: int = 0
    bytes_stored: int = 0
    memory_objects: int = 0
    relations_stored: int = 0
    index_size_bytes: int = 0
    recall_candidates_examined: int = 0
    context_tokens_produced: int = 0
    retrieval_cpu_ms: float = 0.0
    retrieval_wall_ms: float = 0.0
    memory_update_cost: int = 0
    measurement_notes: str = "CPU/GPU/energy/API cost are unavailable for the dependency-free runner."

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResourceMeter:
    def __init__(self) -> None:
        self.usage = ResourceUsage()
        self.started = time.perf_counter()

    def model_call(self, input_text: str, output_text: str) -> None:
        self.usage.input_tokens += max(1, len(input_text.split()))
        self.usage.output_tokens += max(1, len(output_text.split()))
        self.usage.model_invocations += 1

    def communication(self, byte_count: int) -> None:
        self.usage.communication_bytes += int(byte_count)

    def action(self) -> None:
        self.communication(64)

    def memory_update(self, *, objects: int, bytes_stored: int, relations: int = 0) -> None:
        self.usage.memory_objects += int(objects)
        self.usage.bytes_stored += int(bytes_stored)
        self.usage.relations_stored += int(relations)
        self.usage.memory_update_cost += int(objects + relations)

    def recall(self, *, candidates: int, context_tokens: int, latency_ms: float) -> None:
        self.usage.recall_candidates_examined += int(candidates)
        self.usage.context_tokens_produced += int(context_tokens)
        self.usage.retrieval_cpu_ms += round(float(latency_ms), 3)
        self.usage.retrieval_wall_ms += round(float(latency_ms), 3)

    def finish(self) -> ResourceUsage:
        self.usage.wall_clock_ms = round((time.perf_counter() - self.started) * 1000.0, 3)
        return self.usage


def hardware_metadata() -> dict[str, str]:
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "processor": platform.processor() or "unknown",
    }
