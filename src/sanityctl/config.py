from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import CheckSpec, JsonAssertion, TextAssertion


def _text_assertions_from_expect(expect: dict[str, Any]) -> list[TextAssertion]:
    assertions: list[TextAssertion] = []
    stdout = expect.get("stdout", [])
    for item in stdout:
        assertions.append(TextAssertion(op=str(item["op"]), value=str(item["value"])))
    return assertions


def _json_assertions_from_expect(expect: dict[str, Any]) -> list[JsonAssertion]:
    assertions: list[JsonAssertion] = []
    json_items = expect.get("json", [])
    for item in json_items:
        assertions.append(
            JsonAssertion(
                path=str(item["path"]),
                op=str(item["op"]),
                value=item.get("value"),
            )
        )
    return assertions


def load_checks(path: str) -> tuple[list[CheckSpec], dict[str, str]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    checks_data = data.get("checks", [])
    report = data.get("report", {})
    status_labels = report.get("status_labels", {})

    checks: list[CheckSpec] = []
    for item in checks_data:
        expect = item.get("expect", {})
        checks.append(
            CheckSpec(
                name=str(item["name"]),
                cmd=str(item["cmd"]),
                parser=str(item.get("parser", "text")),
                expect_code=int(expect.get("code", item.get("expect_code", 0))),
                stdout_assertions=_text_assertions_from_expect(expect),
                json_assertions=_json_assertions_from_expect(expect),
                timeout=item.get("timeout"),
                env={str(k): str(v) for k, v in item.get("env", {}).items()},
                workdir=item.get("workdir"),
            )
        )

    return checks, {
        "passed": str(status_labels.get("passed", "PASS")),
        "failed": str(status_labels.get("failed", "FAIL")),
    }
