"""Deterministic, dependency-free preregistered statistical helpers."""

from __future__ import annotations

from hashlib import sha256
from typing import Iterable


def _rng(seed: int):
    """Yield deterministic pseudo-random indices without importing a package."""

    counter = 0
    while True:
        digest = sha256(f"{seed}:{counter}".encode("utf-8")).digest()
        counter += 1
        for offset in range(0, len(digest), 4):
            yield int.from_bytes(digest[offset : offset + 4], "big")


def bootstrap_mean_difference(
    left: Iterable[float], right: Iterable[float], *, resamples: int = 10000, seed: int = 17
) -> tuple[float, float, float]:
    """Return observed paired mean difference and percentile 95% interval."""

    left, right = tuple(left), tuple(right)
    if len(left) != len(right) or not left:
        raise ValueError("paired bootstrap inputs must be non-empty and equal length")
    differences = tuple(a - b for a, b in zip(left, right))
    observed = sum(differences) / len(differences)
    generator = _rng(seed)
    samples = []
    for _ in range(resamples):
        indices = [next(generator) % len(differences) for _ in differences]
        samples.append(sum(differences[index] for index in indices) / len(differences))
    samples.sort()
    lower = samples[max(0, int(0.025 * resamples) - 1)]
    upper = samples[min(len(samples) - 1, int(0.975 * resamples))]
    return round(observed, 6), round(lower, 6), round(upper, 6)


def holm_adjust(p_values: Iterable[float]) -> tuple[float, ...]:
    """Apply Holm step-down adjustment while preserving input order."""

    values = tuple(float(value) for value in p_values)
    if any(value < 0.0 or value > 1.0 for value in values):
        raise ValueError("p-values must be between 0 and 1")
    order = sorted(range(len(values)), key=lambda index: values[index])
    adjusted = [0.0] * len(values)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(values) - rank) * values[index])
        adjusted[index] = min(1.0, running)
    return tuple(round(value, 6) for value in adjusted)
