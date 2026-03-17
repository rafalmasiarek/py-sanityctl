from __future__ import annotations

import json
import re
from typing import Any

from .models import JsonAssertion, TextAssertion
from .utils import resolve_json_path


def check_text_assertion(actual: str, assertion: TextAssertion) -> str | None:
    op = assertion.op
    expected = assertion.value

    if op == "contains":
        if expected not in actual:
            return f"stdout does not contain {expected!r}"
        return None

    if op == "equals":
        if actual != expected:
            return f"stdout is not equal to {expected!r}"
        return None

    if op == "regex":
        if re.search(expected, actual, re.MULTILINE) is None:
            return f"stdout does not match regex {expected!r}"
        return None

    return f"unsupported text assertion op: {op}"


def check_json_assertion(data: Any, assertion: JsonAssertion) -> str | None:
    try:
        actual = resolve_json_path(data, assertion.path)
    except Exception as exc:
        return f"json path {assertion.path!r} not found: {exc}"

    op = assertion.op
    expected = assertion.value

    if op == "exists":
        return None

    if op == "equals":
        if actual != expected:
            return f"json path {assertion.path!r} expected {expected!r}, got {actual!r}"
        return None

    if op == "contains":
        if str(expected) not in str(actual):
            return f"json path {assertion.path!r} does not contain {expected!r}"
        return None

    if op == "startswith":
        if not str(actual).startswith(str(expected)):
            return f"json path {assertion.path!r} does not start with {expected!r}"
        return None

    if op == "regex":
        if re.search(str(expected), str(actual), re.MULTILINE) is None:
            return f"json path {assertion.path!r} does not match regex {expected!r}"
        return None

    return f"unsupported json assertion op: {op}"


def parse_json_output(text: str) -> Any:
    return json.loads(text)
