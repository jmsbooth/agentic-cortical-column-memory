"""Registered metric calculations over structured task records."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any, Iterable


FAILURE_CATEGORIES = (
    "base_model_knowledge_failure",
    "retrieval_failure",
    "reference_frame_localization_failure",
    "incorrect_state_transformation",
    "memory_contamination",
    "evidence_selection_failure",
    "hypothesis_generation_failure",
    "consensus_failure",
    "premature_convergence",
    "overconfidence",
    "tool_failure",
    "orchestration_failure",
    "context_exhaustion",
    "compute_budget_exhaustion",
)


def classify_failure(record: dict[str, Any]) -> str | None:
    if record.get("task_success"):
        return None
    status = record.get("final_status")
    if status in {"unresolved", "abstained"}:
        if record.get("task_class") == "incomplete_information":
            return "hypothesis_generation_failure"
        if record.get("actions_available") and not record.get("action_ids"):
            return "evidence_selection_failure"
        return "consensus_failure"
    if status == "committed" and record.get("final_answer") != record.get("ground_truth"):
        if record.get("action_ids") and not record.get("required_observation_retrieved"):
            return "retrieval_failure"
        if not record.get("evidence_ids"):
            return "base_model_knowledge_failure"
        return "premature_convergence"
    return "orchestration_failure"


def _calibration(records: list[dict[str, Any]], bins: int = 10) -> float:
    if not records:
        return 0.0
    total = 0.0
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        bucket = [
            item for item in records
            if lower <= float(item.get("final_confidence", 0.0)) < upper
            or (index == bins - 1 and float(item.get("final_confidence", 0.0)) == upper)
        ]
        if bucket:
            total += abs(mean(float(item.get("final_confidence", 0.0)) for item in bucket) - mean(
                1.0 if item.get("task_success") else 0.0 for item in bucket
            )) * len(bucket) / len(records)
    return round(total, 6)


def summarize_records(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    records = list(records)
    by_strategy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_strategy[record["strategy"]].append(record)
    summaries: dict[str, Any] = {}
    for strategy, items in sorted(by_strategy.items()):
        successes = sum(1 for item in items if item.get("task_success"))
        committed = [item for item in items if item.get("final_status") == "committed"]
        false_consensus = sum(
            1 for item in committed if item.get("final_answer") != item.get("ground_truth")
        )
        retrieved = sum(len(item.get("retrieved_observation_ids", [])) for item in items)
        relevant_retrieved = sum(
            len(set(item.get("retrieved_observation_ids", [])) & set(item.get("required_observation_ids", [])))
            for item in items
        )
        required = sum(len(item.get("required_observation_ids", [])) for item in items)
        actions = sum(len(item.get("action_ids", [])) for item in items)
        useful_actions = sum(
            1 for item in items if set(item.get("action_ids", [])) and item.get("required_observation_retrieved")
        )
        usage = [item.get("resources", {}) for item in items]
        categories = Counter(
            item.get("failure_category") for item in items if item.get("failure_category")
        )
        summaries[strategy] = {
            "n": len(items),
            "task_success_rate": round(successes / len(items), 6) if items else 0.0,
            "accuracy_on_committed": round(successes / len(committed), 6) if committed else None,
            "abstention_rate": round(sum(item.get("final_status") == "abstained" for item in items) / len(items), 6) if items else 0.0,
            "unresolved_rate": round(sum(item.get("final_status") == "unresolved" for item in items) / len(items), 6) if items else 0.0,
            "false_consensus_rate": round(false_consensus / len(committed), 6) if committed else 0.0,
            "expected_calibration_error": _calibration(items),
            "memory_retrieval_precision": round(relevant_retrieved / retrieved, 6) if retrieved else None,
            "memory_retrieval_recall": round(relevant_retrieved / required, 6) if required else None,
            "action_efficiency": round(useful_actions / actions, 6) if actions else None,
            "evidence_utilization_rate": round(useful_actions / len(items), 6) if items else 0.0,
            "mean_convergence_steps": round(mean(item.get("steps", 0) for item in items), 6) if items else 0.0,
            "mean_model_invocations": round(mean(item.get("resources", {}).get("model_invocations", 0) for item in items), 6) if items else 0.0,
            "mean_wall_clock_ms": round(mean(item.get("resources", {}).get("wall_clock_ms", 0.0) for item in items), 6) if items else 0.0,
            "mean_communication_bytes": round(mean(item.get("resources", {}).get("communication_bytes", 0) for item in items), 6) if items else 0.0,
            "failure_taxonomy": dict(sorted(categories.items())),
        }
    return {"record_count": len(records), "strategies": summaries}
