from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import CheckSpec, JsonAssertion, TextAssertion
from .utils import expand_env_value


def _text_assertions_from_expect(expect: dict[str, Any]) -> list[TextAssertion]:
    assertions: list[TextAssertion] = []
    stdout = expect.get("stdout", [])

    for item in stdout:
        assertions.append(
            TextAssertion(
                op=str(item["op"]),
                value=str(item["value"]),
            )
        )

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


def _deep_merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)

    for key, value in override.items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = _deep_merge_dicts(merged[key], value)
        else:
            merged[key] = value

    return merged


def _normalize_includes(raw: Any) -> list[str]:
    if raw is None:
        return []

    if isinstance(raw, str):
        return [raw]

    if isinstance(raw, list):
        includes: list[str] = []
        for item in raw:
            if not isinstance(item, str):
                raise ValueError("include/includes entries must be strings")
            includes.append(item)
        return includes

    raise ValueError("include/includes must be a string or a list of strings")


def _read_yaml_file(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    if not isinstance(data, dict):
        raise ValueError(f"YAML root in {path} must be a mapping/object")

    return expand_env_value(data)


def _load_config_tree(path: Path, stack: set[Path] | None = None) -> dict[str, Any]:
    resolved = path.resolve()
    stack = set() if stack is None else stack

    if resolved in stack:
        chain = " -> ".join(str(p) for p in [*stack, resolved])
        raise ValueError(f"Detected recursive include chain: {chain}")

    stack.add(resolved)
    data = _read_yaml_file(resolved)

    include_raw = data.pop("include", None)
    includes_raw = data.pop("includes", None)

    include_paths = _normalize_includes(include_raw) + _normalize_includes(includes_raw)

    merged: dict[str, Any] = {}

    for include_item in include_paths:
        include_path = Path(include_item)
        if not include_path.is_absolute():
            include_path = (resolved.parent / include_path).resolve()

        included_data = _load_config_tree(include_path, stack=stack)
        merged = _deep_merge_dicts(merged, included_data)

    merged = _deep_merge_dicts(merged, data)

    stack.remove(resolved)
    return merged


def load_checks(path: str) -> tuple[list[CheckSpec], dict[str, str]]:
    data = _load_config_tree(Path(path))

    checks_data = data.get("checks", [])
    if not isinstance(checks_data, list):
        raise ValueError("checks must be a list")

    report = data.get("report", {})
    if report is None:
        report = {}
    if not isinstance(report, dict):
        raise ValueError("report must be a mapping/object")

    status_labels = report.get("status_labels", {})
    if status_labels is None:
        status_labels = {}
    if not isinstance(status_labels, dict):
        raise ValueError("report.status_labels must be a mapping/object")

    checks: list[CheckSpec] = []

    for item in checks_data:
        if not isinstance(item, dict):
            raise ValueError("each check must be a mapping/object")

        expect = item.get("expect", {})
        if expect is None:
            expect = {}
        if not isinstance(expect, dict):
            raise ValueError(f"expect for check {item!r} must be a mapping/object")

        env = item.get("env", {})
        if env is None:
            env = {}
        if not isinstance(env, dict):
            raise ValueError(f"env for check {item!r} must be a mapping/object")

        checks.append(
            CheckSpec(
                name=str(item["name"]),
                cmd=str(item["cmd"]),
                parser=str(item.get("parser", "text")),
                expect_code=int(expect.get("code", item.get("expect_code", 0))),
                stdout_assertions=_text_assertions_from_expect(expect),
                json_assertions=_json_assertions_from_expect(expect),
                timeout=item.get("timeout"),
                env={str(k): str(v) for k, v in env.items()},
                workdir=str(item["workdir"]) if item.get("workdir") is not None else None,
            )
        )

    return checks, {
        "passed": str(status_labels.get("passed", "PASS")),
        "failed": str(status_labels.get("failed", "FAIL")),
    }