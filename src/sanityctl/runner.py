from __future__ import annotations

import os
import subprocess
import time

from .assertions import check_json_assertion, check_text_assertion, parse_json_output
from .models import CheckResult, CheckSpec, RunResult


def run_check(spec: CheckSpec, passed_label: str = "PASS", failed_label: str = "FAIL") -> CheckResult:
    start = time.perf_counter()

    env = os.environ.copy()
    env.update(spec.env)

    proc = subprocess.run(
        spec.cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=spec.timeout,
        cwd=spec.workdir,
        env=env,
    )

    duration_ms = int((time.perf_counter() - start) * 1000)

    failures: list[str] = []

    if proc.returncode != spec.expect_code:
        failures.append(f"expected exit code {spec.expect_code}, got {proc.returncode}")

    for assertion in spec.stdout_assertions:
        failure = check_text_assertion(proc.stdout, assertion)
        if failure:
            failures.append(failure)

    if spec.parser == "json":
        try:
            data = parse_json_output(proc.stdout)
        except Exception as exc:
            failures.append(f"failed to parse stdout as json: {exc}")
        else:
            for assertion in spec.json_assertions:
                failure = check_json_assertion(data, assertion)
                if failure:
                    failures.append(failure)

    passed = len(failures) == 0
    return CheckResult(
        name=spec.name,
        passed=passed,
        status=passed_label if passed else failed_label,
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        duration_ms=duration_ms,
        failures=failures,
    )


def run_checks(
    checks: list[CheckSpec],
    passed_label: str = "PASS",
    failed_label: str = "FAIL",
) -> RunResult:
    results = [run_check(c, passed_label=passed_label, failed_label=failed_label) for c in checks]
    return RunResult(checks=results, passed_label=passed_label, failed_label=failed_label)
