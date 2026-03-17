from __future__ import annotations

from typing import Any


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
            tokens.append(path[i + 1:end])
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
