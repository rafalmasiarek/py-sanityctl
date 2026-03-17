from __future__ import annotations

import json

from .models import RunResult


def render_output_text(result: RunResult) -> str:
    lines: list[str] = []
    for check in result.checks:
        lines.append(f"{check.status} {check.name}")
    return "\n".join(lines)


def render_output_json(result: RunResult) -> str:
    payload = {
        "summary": {
            "total": result.total,
            "passed": result.passed_count,
            "failed": result.failed_count,
            "status": result.overall_status,
        },
        "checks": [
            {
                "name": c.name,
                "passed": c.passed,
                "status": c.status,
                "exit_code": c.exit_code,
                "duration_ms": c.duration_ms,
                "failures": c.failures,
            }
            for c in result.checks
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def render_summary_text(result: RunResult) -> str:
    return f"{result.total} checks, {result.passed_count} passed, {result.failed_count} failed"


def render_summary_table(result: RunResult) -> str:
    headers = ["Check", "Status", "Exit Code", "Duration ms"]
    rows = [
        [c.name, c.status, str(c.exit_code), str(c.duration_ms)]
        for c in result.checks
    ]

    widths = [len(h) for h in headers]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(value))

    def border() -> str:
        return "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def fmt_row(values: list[str]) -> str:
        return "| " + " | ".join(v.ljust(widths[i]) for i, v in enumerate(values)) + " |"

    parts = [border(), fmt_row(headers), border()]
    for row in rows:
        parts.append(fmt_row(row))
    parts.append(border())
    return "\n".join(parts)


def render_summary_markdown(result: RunResult) -> str:
    lines = [
        "| Check | Status | Exit Code | Duration ms |",
        "|---|---|---:|---:|",
    ]
    for c in result.checks:
        safe_name = c.name.replace("|", "\\|")
        safe_status = c.status.replace("|", "\\|")
        lines.append(f"| {safe_name} | {safe_status} | {c.exit_code} | {c.duration_ms} |")
    return "\n".join(lines)
