"""Run a configured deterministic experiment and emit a complete manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluation.metrics.metrics import classify_failure
from evaluation.resource_accounting.accounting import hardware_metadata
from experiments.baselines.strategies import STRATEGIES, run_strategy
from experiments.tasks.synthetic_world import TASK_VERSION, build_suite


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _config_hash(config: dict[str, Any]) -> str:
    payload = json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _record(task: Any, strategy: str, trace: dict[str, Any], usage: Any, config: dict[str, Any], seed: int, config_hash: str, git_commit: str | None) -> dict[str, Any]:
    final_status = trace.get("status", "orchestration_error")
    final_answer = trace.get("answer")
    retrieved_ids = [
        item["object_id"] for item in trace.get("memory", []) if item.get("operation") == "retrieve"
    ]
    required_ids = list(task.required_observation_ids)
    evidence_ids = []
    for vote in trace.get("votes", []):
        evidence_ids.extend(vote.get("hypothesis", {}).get("evidence_ids", []))
    recall_blocks = trace.get("recall", [])
    if isinstance(recall_blocks, dict):
        recall_blocks = []
    recalled_provenance = {
        provenance
        for block in recall_blocks
        for provenance in block.get("context", {}).get("provenance", [])
    }
    record = {
        "experiment_id": config["experiment_id"],
        "protocol_version": config["protocol_version"],
        "configuration_hash": config_hash,
        "git_commit": git_commit,
        "model_version": config["model"]["version"],
        "task_version": TASK_VERSION,
        "hardware": hardware_metadata(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "random_seed": seed,
        "strategy": strategy,
        "task_id": task.task_id,
        "task_class": task.task_class,
        "ground_truth": task.answer,
        "final_status": final_status,
        "final_answer": final_answer,
        "final_confidence": trace.get("confidence", 0.0),
        "task_success": final_status == "committed" and final_answer == task.answer,
        "actions_available": bool(task.actions),
        "action_ids": [item["action_id"] for item in trace.get("actions", [])],
        "required_observation_ids": required_ids,
        "retrieved_observation_ids": retrieved_ids,
        "required_observation_retrieved": bool(set(required_ids) & set(retrieved_ids)),
        "provenance_recalled": bool(recalled_provenance),
        "recalled_provenance": sorted(recalled_provenance),
        "context_tokens_produced": usage.context_tokens_produced,
        "evidence_ids": sorted(set(evidence_ids)),
        "steps": trace.get("steps", 0),
        "failure_category": None,
        "resources": usage.to_dict(),
        "trace": trace,
    }
    record["failure_category"] = classify_failure(record)
    return record


def run_config(config: dict[str, Any], output_dir: Path, manifest_dir: Path | None = None) -> tuple[Path, Path]:
    strategies = tuple(config["strategies"])
    invalid = sorted(set(strategies) - set(STRATEGIES))
    if invalid:
        raise ValueError(f"unknown strategies in config: {invalid}")
    config_hash = _config_hash(config)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / f"{config['experiment_id']}.jsonl"
    manifest_path = (manifest_dir or Path("results/manifests")) / f"{config['experiment_id']}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    git_commit = _git_commit()
    records = []
    for seed in config["seeds"]:
        tasks = build_suite(seed, config["task_classes"], config["tasks_per_class"])
        for task in tasks:
            for strategy in strategies:
                trace, meter = run_strategy(task, strategy, seed)
                usage = meter.finish()
                records.append(_record(task, strategy, trace, usage, config, seed, config_hash, git_commit))
    with raw_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    manifest = {
        "manifest_version": "0.1.0",
        "experiment_id": config["experiment_id"],
        "protocol_version": config["protocol_version"],
        "configuration_hash": config_hash,
        "git_commit": git_commit,
        "model": config["model"],
        "task_version": TASK_VERSION,
        "hardware": hardware_metadata(),
        "python": platform.python_version(),
        "seeds": config["seeds"],
        "status": "smoke_validation" if config.get("run_kind") == "smoke" else "registered_execution",
        "record_count": len(records),
        "raw_results": str(raw_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": config,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return raw_path, manifest_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("results/raw"))
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    raw_path, manifest_path = run_config(config, args.output_dir)
    print(json.dumps({"raw_results": str(raw_path), "manifest": str(manifest_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
