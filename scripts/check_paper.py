#!/usr/bin/env python3
"""Cheap source-level guard against stale placeholders and broken inputs."""

from pathlib import Path


def main() -> int:
    source = Path("paper/main.tex").read_text(encoding="utf-8")
    if "RESULT TBD" in source or "Prepared for James Booth" in source:
        raise SystemExit("stale publication placeholder found")
    for required in ("sections/01_introduction", "sections/03_ccm", "sections/05_experimental_design", "refs"):
        if required not in source:
            raise SystemExit(f"paper input missing: {required}")
    print("paper source checks OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
