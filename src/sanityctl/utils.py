from __future__ import annotations

import os
from typing import Any


def expand_env_string(value: str) -> str:
    """Expand $VAR and ${VAR} placeholders using the current process environment."""
    return os.path.expandvars(value)


def expand_env_value(value: Any) -> Any:
    """Recursively expand environment variables in strings, lists, and dicts."""
    if isinstance(value, str):
        return expand_env_string(value)

    if isinstance(value, list):
        return [expand_env_value(item) for item in value]

    if isinstance(value, dict):
        return {key: expand_env_value(item) for key, item in value.items()}

    return value


def resolve_json_path(data: Any, path: str) -> Any:
    if not path:
        return data

    tokens: list[str] = []
    buf = ""
    i = 0

    while i < len(path):
        ch = path[i]

        if ch == ".":
            if buf:
                tokens.append(buf)
                buf = ""
            i += 1
            continue

        if ch == "[":
            if buf:
                tokens.append(buf)
                buf = ""
            end = path.find("]", i)
            if end == -1:
                raise ValueError(f"Invalid path: {path}")
            tokens.append(path[i + 1 : end])
            i = end + 1
            continue

        buf += ch
        i += 1

    if buf:
        tokens.append(buf)

    current = data
    for token in tokens:
        if isinstance(current, list):
            idx = int(token)
            current = current[idx]
        elif isinstance(current, dict):
            current = current[token]
        else:
            raise KeyError(token)

    return current