#!/usr/bin/env python3
"""Perform exact-HEAD local Phase 1A regression checks in a disposable git worktree.

Never use a GitHub-hosted CI check as evidence for a local run. Never classify
symbolic smoke runs as empirical performance evidence. Logs preserve failures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def run_command(name: str, argv: list[str], cwd: Path, evidence: Path, expected_exit: int = 0) -> dict[str, object]:
    log = evidence / f"{name}.log"
    started = utc()
    try:
        result = subprocess.run(argv, cwd=cwd, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                errors="replace", timeout=600)
        returncode = result.returncode
        output = result.stdout
    except (OSError, subprocess.TimeoutExpired) as exc:
        returncode = 125
        output = f"LOCAL EXECUTION FAILURE: {type(exc).__name__}: {exc}\n"
    ended = utc()
    text = (f"$ {' '.join(argv)}\nSTART_UTC={started}\nEND_UTC={ended}\n"
            + output + f"\nEXIT_CODE={returncode}\nEXPECTED_EXIT_CODE={expected_exit}\n")
    log.write_text(text, encoding="utf-8")
    outcome = "PASS" if returncode == expected_exit else "FAIL"
    found = re.search(r"Ran (\d+) tests? in", text)
    tests = int(found.group(1)) if found else None
    validation_note = "exit code matched" if outcome == "PASS" else "unexpected exit code"
    if name == "unittest" and (tests is None or tests < 18):
        outcome, validation_note = "FAIL", "missing or incomplete unittest discovery"
    if name in {"preflight-smoke", "preflight-block-legacy", "registered-runner-block"}:
        # Exit status 2 alone can be a missing interpreter/script, not a correct block.
        try:
            payload = json.loads(output)
            checks = {item.get("id"): item.get("status") for item in payload.get("checks", [])}
            safe = payload.get("protocol_id") == "CCM-EMP-002" and payload.get("eligible_for_empirical") is False
            if name == "preflight-smoke":
                safe = safe and payload.get("ok") is True and payload.get("result_classification") == "software_validation_only"
            else:
                safe = (safe and payload.get("ok") is False and
                        all(checks.get(x) == "blocked" for x in
                            ("baseline_fidelity", "real_model_required", "registered_runner_qualified")))
            if not safe:
                outcome, validation_note = "FAIL", "preflight JSON lacks required guard evidence"
        except (ValueError, TypeError, AttributeError):
            outcome, validation_note = "FAIL", "preflight did not emit valid JSON guard evidence"
    if name == "smoke-shape" and not re.search(r"validated [1-9][0-9]* smoke records", output):
        outcome, validation_note = "FAIL", "smoke shape validator did not validate nonempty records"
    if name == "paper-check" and "paper source checks OK" not in output:
        outcome, validation_note = "FAIL", "paper checker did not emit success marker"
    if name == "smoke":
        expected_raw = cwd / "out" / "raw" / "ccm-smoke-v0.1.0.jsonl"
        if not expected_raw.exists() or expected_raw.stat().st_size == 0:
            outcome, validation_note = "FAIL", "smoke did not generate nonempty raw records"
    if name == "compileall" and not all((cwd / x).is_dir() for x in ("ccm", "experiments", "evaluation", "tests")):
        outcome, validation_note = "FAIL", "source directories missing; compileall exit 0 is insufficient"
    return {"name": name, "argv": argv, "log": log.name,
            "started_utc": started, "ended_utc": ended, "exit_code": returncode,
            "expected_exit_code": expected_exit, "outcome": outcome,
            "test_count": tests, "sha256": sha256(log), "validation_note": validation_note}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--expected-sha", help="Reject any different HEAD before executing")
    parser.add_argument("--evidence-root", type=Path, help="Where to write raw evidence")
    args = parser.parse_args()
    repo = args.repo.resolve()
    try:
        actual = git("rev-parse", "HEAD", cwd=repo)
        root = Path(git("rev-parse", "--show-toplevel", cwd=repo)).resolve()
    except (OSError, subprocess.CalledProcessError) as exc:
        parser.error(f"not a complete local Git checkout: {exc}")
    if root != repo:
        parser.error(f"--repo must identify the Git repository root: {root}")
    if args.expected_sha and actual != args.expected_sha:
        parser.error(f"HEAD mismatch: expected {args.expected_sha}, found {actual}")
    evidence = (args.evidence_root.resolve() if args.evidence_root else
                root / "evidence" / "ccm-v0.2.0" / "validation" / ("exact-head-" + actual[:12]))
    if evidence.exists() and any(evidence.iterdir()):
        parser.error("evidence directory already populated; never overwrite test evidence")
    evidence.mkdir(parents=True, exist_ok=True)
    run_start = utc()
    with tempfile.TemporaryDirectory(prefix="ccm-exact-head-") as temporary:
        worktree = Path(temporary) / "src"
        subprocess.run(["git", "worktree", "add", "--detach", str(worktree), actual],
                       cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            python = sys.executable
            tasks = [
                ("compileall", [python, "-m", "compileall", "-q", "ccm", "experiments", "evaluation", "tests"], 0),
                ("unittest", [python, "-m", "unittest", "discover", "-s", "tests", "-t", ".", "-v"], 0),
                ("smoke", ["bash", "scripts/run_smoke", "--output-dir", str(worktree / "out" / "raw")], 0),
                ("smoke-shape", [python, "scripts/check_smoke.py", str(worktree / "out" / "raw" / "ccm-smoke-v0.1.0.jsonl")], 0),
                ("preflight-smoke", [python, "scripts/ccm_preflight", "--config", "experiments/configs/smoke_v0.1.0.json"], 0),
                ("preflight-block-legacy", [python, "scripts/ccm_preflight", "--config", "preregistration/registered-configs/ccm-v0.1.0.json"], 2),
                ("registered-runner-block", ["bash", "scripts/run_registered"], 2),
                ("paper-check", [python, "scripts/check_paper.py"], 0),
            ]
            records = [run_command(name, argv, worktree, evidence, code) for name,argv,code in tasks]
            status = "PASS" if all(r["outcome"] == "PASS" for r in records) else "FAIL"
            try:
                worktree_head = git("rev-parse", "HEAD", cwd=worktree)
            except subprocess.CalledProcessError:
                worktree_head = None
            if worktree_head != actual:
                status = "FAIL"
            manifest = {"protocol": "CCM-EMP-002", "stage": "Phase 1A exact-head local regression",
                        "classification": "local_software_validation_only", "status": status,
                        "head_sha": actual, "worktree_sha": worktree_head,
                        "host": {"platform": platform.platform(), "python": platform.python_version(), "architecture": platform.machine()},
                        "start_utc": run_start, "end_utc": utc(), "runs": records,
                        "assertions": {"no_empirical_effectiveness_claim": True, "tested_exact_git_head": worktree_head == actual}}
            (evidence / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            manifest_files = sorted(p for p in evidence.iterdir() if p.is_file())
            (evidence / "SHA256SUMS.txt").write_text("".join(f"{sha256(p)}  {p.name}\n" for p in manifest_files), encoding="utf-8")
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=root, check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(json.dumps({"status": status, "head_sha": actual, "evidence": str(evidence)}, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
