#!/usr/bin/env python3
"""CI check for complete smoke records without depending on result values."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED = {
    "experiment_id", "configuration_hash", "git_commit", "model_version", "task_version",
    "random_seed", "strategy", "task_class", "final_status", "resources", "trace",
}


def main(path: str) -> int:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    if not lines:
        raise SystemExit("smoke output is empty")
    for index, line in enumerate(lines, 1):
        record = json.loads(line)
        missing = sorted(REQUIRED - record.keys())
        if missing:
            raise SystemExit(f"record {index} missing {missing}")
        if record["resources"]["model_invocations"] < 1:
            raise SystemExit(f"record {index} has no model invocation")
    print(f"validated {len(lines)} smoke records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
