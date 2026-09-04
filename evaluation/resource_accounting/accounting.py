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

    def finish(self) -> ResourceUsage:
        self.usage.wall_clock_ms = round((time.perf_counter() - self.started) * 1000.0, 3)
        return self.usage


def hardware_metadata() -> dict[str, str]:
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "processor": platform.processor() or "unknown",
    }
