from sanityctl.models import CheckSpec
from sanityctl.runner import run_checks


def test_run_checks_smoke():
    checks = [
        CheckSpec(name="ok", cmd="python -c 'print(\"hello\")'"),
    ]
    result = run_checks(checks)
    assert result.total == 1
    assert result.passed_count == 1
    assert result.failed_count == 0
