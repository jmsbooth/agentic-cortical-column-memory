"""Small dependency-free SVG figures generated from processed summaries."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


def write_success_bar_chart(summary: dict[str, Any], path: Path) -> None:
    rows = sorted(summary.get("strategies", {}).items())
    width, height = 760, max(180, 80 + 28 * len(rows))
    left, top, chart_width, row_height = 190, 35, 520, 24
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font:12px sans-serif;fill:#222}.title{font-weight:700}.bar{fill:#3b82f6}</style>',
        '<text class="title" x="20" y="20">Task-success rate by strategy (generated artifact)</text>',
    ]
    for index, (strategy, values) in enumerate(rows):
        y = top + index * row_height
        rate = max(0.0, min(1.0, float(values.get("task_success_rate", 0.0))))
        svg.append(f'<text x="{left - 8}" y="{y + 15}" text-anchor="end">{escape(strategy)}</text>')
        svg.append(f'<rect class="bar" x="{left}" y="{y}" width="{chart_width * rate:.2f}" height="16"/>')
        svg.append(f'<text x="{left + chart_width + 8}" y="{y + 15}">{rate:.3f}</text>')
    svg.append(f'<line x1="{left}" y1="{top - 6}" x2="{left}" y2="{height - 20}" stroke="#555"/>')
    svg.append(f'<line x1="{left}" y1="{height - 20}" x2="{left + chart_width}" y2="{height - 20}" stroke="#555"/>')
    svg.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(svg) + "\n", encoding="utf-8")
