from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


ParserType = Literal["text", "json"]
OutputType = Literal["text", "json", "none"]
SummaryType = Literal["text", "table", "markdown"]


@dataclass
class TextAssertion:
    op: str
    value: str


@dataclass
class JsonAssertion:
    path: str
    op: str
    value: Any = None


@dataclass
class CheckSpec:
    name: str
    cmd: str
    parser: ParserType = "text"
    expect_code: int = 0
    stdout_assertions: list[TextAssertion] = field(default_factory=list)
    json_assertions: list[JsonAssertion] = field(default_factory=list)
    timeout: int | None = None
    env: dict[str, str] = field(default_factory=dict)
    workdir: str | None = None


@dataclass
class CheckResult:
    name: str
    passed: bool
    status: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    failures: list[str] = field(default_factory=list)


@dataclass
class RunResult:
    checks: list[CheckResult]
    passed_label: str = "PASS"
    failed_label: str = "FAIL"

    @property
    def total(self) -> int:
        return len(self.checks)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed)

    @property
    def overall_status(self) -> str:
        return self.passed_label if self.failed_count == 0 else self.failed_label
