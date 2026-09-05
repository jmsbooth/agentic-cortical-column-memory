#!/usr/bin/env python3
"""Cheap source-level guard against stale placeholders and broken inputs."""

from pathlib import Path


def main() -> int:
    source = Path("paper/main.tex").read_text(encoding="utf-8")
    sections = "\n".join(path.read_text(encoding="utf-8") for path in Path("paper/sections").glob("*.tex"))
    searchable = source + "\n" + sections
    stale_markers = (
        "RESULT TBD",
        "Prepared for James Booth",
        "Resource-Constrained Multi-Agent Systems",
        "TPAA integration context",
        "agentic-cortical-column-memory",
    )
    if any(marker in searchable for marker in stale_markers):
        raise SystemExit("stale publication placeholder found")
    for required in (
        "sections/01_introduction",
        "sections/03_ccm",
        "sections/04_problem_definition",
        "sections/05_experimental_design",
        "fig:multi-agent",
        "refs",
    ):
        if required not in searchable:
            raise SystemExit(f"paper input missing: {required}")
    print("paper source checks OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
