"""CCM-EMP-002 prospective local empirical validity gate.

This module intentionally rejects unqualified real-model experiments. Its
success for a symbolic smoke configuration means SOFTWARE VALIDATION ONLY.
"""
from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import fields
from pathlib import Path
from typing import Any

from ccm.empirical.contracts import BoundaryViolation, ModelVisibleCase
from experiments.empirical.cases import make_boundary_fixture


EMPIRICAL_RUN_KINDS = frozenset({"registered", "confirmatory", "pilot", "empirical"})
LEGACY_MODEL_MARKERS = ("toy", "symbolic", "smoke", "oracle")
PROTOCOL_PATH = "preregistration/ccm-v0.2.0/PROTOCOL.md"
LOCK_PATH = "preregistration/ccm-v0.2.0/protocol-lock.json"
BASELINES_PATH = "experiments/empirical/baseline_registry.json"
SOURCE_ALLOWLIST = ("ccm/empirical/contracts.py", "ccm/adapters/empirical.py")


def validate_visible_source(root: Path) -> list[str]:
    failures = []
    for rel in SOURCE_ALLOWLIST:
        path = root / rel
        if not path.is_file():
            failures.append(f"missing boundary source {rel}")
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except SyntaxError as error:
            failures.append(f"syntax error in boundary source {rel}: {error}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and (
                node.module.startswith("evaluation.empirical.oracles") or
                node.module.startswith("experiments.baselines")
            ):
                failures.append(f"forbidden evaluator/legacy import in {rel}")
            if isinstance(node, ast.Import) and any(
                alias.name.startswith("evaluation.empirical.oracles") or alias.name.startswith("experiments.baselines")
                for alias in node.names
            ):
                failures.append(f"forbidden evaluator/legacy import in {rel}")
            if isinstance(node, ast.Attribute) and node.attr in {"answer", "gold_answer", "ground_truth", "task_success"}:
                failures.append(f"unauthorized evaluator-style attribute .{node.attr} in {rel}")
    return failures


def _is_legacy_model(config: dict[str, Any]) -> bool:
    model = config.get("model", {})
    if not isinstance(model, dict):
        return True
    combined = " ".join(str(model.get(k, "")) for k in ("family", "version", "revision", "adapter", "backend", "provider"))
    return any(marker in combined.lower() for marker in LEGACY_MODEL_MARKERS)


def assess_configuration(config: dict[str, Any], *, root: Path) -> dict[str, Any]:
    """Return deterministic, machine-readable preflight checks (never a benchmark result)."""
    checks: list[dict[str, str]] = []

    def check(identifier: str, ok: bool, detail: str) -> None:
        checks.append({"id": identifier, "status": "pass" if ok else "blocked", "detail": detail})

    run_kind = config.get("run_kind", "missing")
    empirical = run_kind in EMPIRICAL_RUN_KINDS
    check("run_kind_recognized", run_kind in EMPIRICAL_RUN_KINDS | {"smoke"}, f"run_kind={run_kind}")

    protocol_file = root / PROTOCOL_PATH
    lock_file = root / LOCK_PATH
    valid_protocol = False
    protocol_digest = "unavailable"
    if protocol_file.is_file() and lock_file.is_file():
        protocol_digest = hashlib.sha256(protocol_file.read_bytes()).hexdigest()
        try:
            lock = json.loads(lock_file.read_text(encoding="utf-8"))
            valid_protocol = lock.get("sha256") == protocol_digest and lock.get("protocol_id") == "CCM-EMP-002"
        except (ValueError, OSError):
            pass
    check("protocol_integrity", valid_protocol, f"sha256={protocol_digest}")

    schema_fields = {field.name for field in fields(ModelVisibleCase)}
    prohibited = {"answer", "gold_answer", "ground_truth", "expected_answer", "scoring_metadata", "required_evidence_ids"}
    check("visible_schema_allowlist", not (schema_fields & prohibited), "ModelVisibleCase contains no evaluator answer fields")

    source_errors = validate_visible_source(root)
    check("gold_access_allowlist", not source_errors, "; ".join(source_errors) if source_errors else "empirical boundary sources contain no evaluator import or gold reads")

    try:
        visible, evaluator = make_boundary_fixture(107, 1)
        serialized = visible.to_json()
        visible_copy = ModelVisibleCase.from_json(serialized)
        from dataclasses import replace
        alternate_oracle = replace(evaluator, gold_answer="Counterfactual", accepted_answers=("Counterfactual",))
        # A counterfactual grader label cannot affect this independent case payload.
        untouched = alternate_oracle.case_id == evaluator.case_id and visible.to_json() == serialized
        try:
            ModelVisibleCase.from_dict({**visible.to_dict(), "ground_truth": "canary"})
        except BoundaryViolation:
            canary_blocked = True
        else:
            canary_blocked = False
        contract_ok = visible_copy == visible and untouched and canary_blocked
    except Exception as exc:
        contract_ok = False
        fixture_error = repr(exc)
    else:
        fixture_error = "two schema objects remain independently serialized; forbidden field rejected"
    check("fixture_metamorphic_boundary", contract_ok, fixture_error)

    registry_path = root / BASELINES_PATH
    registry = {}
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))["baselines"]
    except (OSError, ValueError, KeyError, TypeError):
        pass
    check("baseline_registry_present", bool(registry), "explicit, inspectable baseline implementation status")

    eligible: list[str] = []
    strategy_ids = config.get("strategies", [])
    if not isinstance(strategy_ids, list):
        strategy_ids = []
    if empirical:
        requested = [s for s in strategy_ids if isinstance(s, str)]
        eligible = [s for s in requested if registry.get(s, {}).get("confirmatory_eligible") is True]
        check("baseline_fidelity", len(requested) > 0 and len(eligible) == len(requested),
              f"qualified={eligible}; requested={requested}; placeholders are not empirical baselines")
        check("real_model_required", not _is_legacy_model(config), "toy/symbolic/smoke models are ineligible for pilot or confirmatory inference")
        # The existing runner imports SyntheticTask and ToyModel. Until phase 1C
        # provides a separately audited empirical runner, block ALL empirical runs.
        check("registered_runner_qualified", False, "existing experiments.runners.run is symbolic; an independent empirical runner is not yet approved")
    else:
        check("symbolic_smoke_only", run_kind == "smoke", "legacy symbolic execution may be labeled software_validation only")

    ok = all(item["status"] == "pass" for item in checks)
    return {
        "protocol_id": "CCM-EMP-002",
        "run_kind": run_kind,
        "result_classification": "unexecuted_empirical_preflight" if empirical else "software_validation_only",
        "eligible_for_empirical": empirical and ok,
        "ok": ok,
        "checks": checks,
    }


def require_qualified_run(config: dict[str, Any], *, root: Path) -> None:
    """The legacy runner must reject empirical/registered configs before execution."""
    if config.get("run_kind") == "smoke":
        return
    report = assess_configuration(config, root=root)
    failures = [item["id"] for item in report["checks"] if item["status"] != "pass"]
    raise ValueError("Empirical execution blocked by CCM-EMP-002: " + ", ".join(failures or ["unqualified_legacy_runner"]))
