from __future__ import annotations

import argparse
import sys
from textwrap import dedent

from rich_argparse import RawDescriptionRichHelpFormatter

from .config import load_checks
from .models import CheckSpec, JsonAssertion, TextAssertion
from .reporters import (
    render_output_json,
    render_output_text,
    render_summary_markdown,
    render_summary_table,
    render_summary_text,
)
from .runner import run_checks
from .utils import expand_env_string


class SanityctlHelpFormatter(RawDescriptionRichHelpFormatter):
    """Rich help formatter that preserves manual line breaks in descriptions/epilogs."""

    width = 110
    max_help_position = 30


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sanityctl",
        description=dedent(
            """
            Run lightweight sanity checks against shell commands.

            sanityctl is designed for simple operational validation:
              • run one command and assert on its output
              • load multiple checks from a YAML configuration file
              • validate plain text stdout
              • validate parsed JSON stdout
              • print results in human-readable or machine-readable form

            Typical use cases:
              • smoke checks in CI/CD
              • validating CLI tools after deployment
              • checking API wrappers that print JSON
              • keeping a small set of "known good" operational checks
            """
        ),
        epilog=dedent(
            """
            Quick start:
              sanityctl run --cmd "printf 'hello'" --stdout-contains hello --summary
              sanityctl run -f examples/checks.yaml --summary table
              sanityctl run -f checks.yaml --output json

            Important notes:
              • Use --file to load checks from YAML.
              • Use --cmd to define one inline check directly on the command line.
              • You can combine both: checks from file + one inline check in the same run.
              • YAML supports include/includes for composing configs.
              • String values support environment expansion like $VAR and ${VAR}.
              • JSON assertions require --parser json and usually --json-path.
              • Exit code 0 means all checks passed.
              • Exit code 1 means at least one check failed.

            Read the subcommand help for full examples:
              sanityctl run --help
            """
        ),
        formatter_class=SanityctlHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        title="commands",
        metavar="{run}",
        help="Available subcommands",
    )

    run = subparsers.add_parser(
        "run",
        help="Run checks from a YAML file and/or a single inline command definition",
        description=dedent(
            """
            Execute one or more sanity checks.

            Input modes:
              1. YAML file mode
                 Load checks from a configuration file with --file.

              2. Inline mode
                 Define a single check directly with --cmd and optional assertion flags.

              3. Combined mode
                 Use both --file and --cmd in one invocation.
                 The inline check is appended to the checks loaded from the file.

            Execution model:
              • each check runs as a shell command
              • the process exit code is validated
              • additional assertions are evaluated against stdout
              • in JSON mode, stdout is parsed before JSON assertions are applied
            """
        ),
        epilog=dedent(
            """
            EXAMPLES

              1) Smallest useful inline text check
                 sanityctl run \
                   --cmd "printf 'hello'" \
                   --stdout-contains hello \
                   --summary

              2) Inline text check with explicit display name
                 sanityctl run \
                   --name "hello smoke test" \
                   --cmd "printf 'hello world'" \
                   --stdout-contains hello \
                   --summary table

              3) Inline JSON check
                 sanityctl run \
                   --cmd "python -c 'import json; print(json.dumps({\"status\": \"ok\", \"version\": \"1.2.3\"}))'" \
                   --parser json \
                   --json-path status \
                   --json-equals ok \
                   --summary

              4) Load checks from YAML
                 sanityctl run -f examples/checks.yaml --summary table

              5) Combine YAML checks with one extra inline check
                 sanityctl run \
                   -f examples/checks.yaml \
                   --name "extra runtime check" \
                   --cmd "printf 'runtime-ok'" \
                   --stdout-contains runtime-ok \
                   --summary table

            YAML CONFIG EXAMPLE

              include:
                - shared/common.yaml

              report:
                status_labels:
                  passed: PASS
                  failed: FAIL

              checks:
                - name: python version
                  cmd: python --version
                  expect:
                    code: 0
                    stdout:
                      - op: contains
                        value: "Python"

                - name: service status
                  cmd: python -c 'import json; print(json.dumps({"status":"ok","version":"1.2.3"}))'
                  parser: json
                  expect:
                    code: 0
                    json:
                      - path: status
                        op: equals
                        value: ok
                      - path: version
                        op: startswith
                        value: "${EXPECTED_VERSION_PREFIX}"

            JSON PATH EXAMPLES

              status
              service.name
              items[0]
              items[0].name

            EXIT STATUS

              0   all checks passed
              1   at least one check failed
            """
        ),
        formatter_class=SanityctlHelpFormatter,
    )

    input_group = run.add_argument_group("input sources")
    input_group.add_argument(
        "-f",
        "--file",
        dest="file_path",
        metavar="PATH",
        help="Path to a YAML configuration file containing one or more checks.",
    )
    input_group.add_argument(
        "--name",
        metavar="TEXT",
        help="Display name for the inline check. Defaults to the command text.",
    )
    input_group.add_argument(
        "--cmd",
        metavar="COMMAND",
        help="Shell command to execute as an inline check.",
    )

    behavior_group = run.add_argument_group("inline check behavior")
    behavior_group.add_argument(
        "--expect-code",
        type=int,
        default=0,
        metavar="N",
        help="Expected process exit code for the inline check.",
    )
    behavior_group.add_argument(
        "--parser",
        choices=["text", "json"],
        default="text",
        help="How stdout from the inline command should be interpreted.",
    )

    text_group = run.add_argument_group("inline text assertions")
    text_group.add_argument(
        "--stdout-contains",
        metavar="TEXT",
        help="Pass only if stdout contains the given substring.",
    )
    text_group.add_argument(
        "--stdout-equals",
        metavar="TEXT",
        help="Pass only if stdout exactly equals the given text.",
    )
    text_group.add_argument(
        "--stdout-regex",
        metavar="REGEX",
        help="Pass only if stdout matches the given regular expression.",
    )

    json_group = run.add_argument_group("inline JSON assertions")
    json_group.add_argument(
        "--json-path",
        metavar="PATH",
        help="JSON path to inspect, e.g. status, service.name, items[0].name.",
    )
    json_group.add_argument(
        "--json-equals",
        metavar="VALUE",
        help="Pass only if the JSON value at --json-path equals VALUE.",
    )
    json_group.add_argument(
        "--json-contains",
        metavar="VALUE",
        help="Pass only if the JSON value at --json-path contains VALUE.",
    )
    json_group.add_argument(
        "--json-regex",
        metavar="REGEX",
        help="Pass only if the JSON value at --json-path matches REGEX.",
    )
    json_group.add_argument(
        "--json-startswith",
        metavar="PREFIX",
        help="Pass only if the JSON value at --json-path starts with PREFIX.",
    )

    output_group = run.add_argument_group("output and presentation")
    output_group.add_argument(
        "--output",
        choices=["text", "json", "none"],
        default="text",
        help="Main output format for per-check results.",
    )
    output_group.add_argument(
        "--summary",
        nargs="?",
        const="text",
        choices=["text", "table", "markdown"],
        help="Append a summary. Without a value, defaults to 'text'.",
    )
    output_group.add_argument(
        "--passed-label",
        metavar="TEXT",
        help="Custom label for passed checks. Overrides the YAML setting.",
    )
    output_group.add_argument(
        "--failed-label",
        metavar="TEXT",
        help="Custom label for failed checks. Overrides the YAML setting.",
    )

    return parser


def inline_check_from_args(args: argparse.Namespace) -> CheckSpec | None:
    if not args.cmd:
        return None

    expanded_cmd = expand_env_string(args.cmd)
    expanded_name = expand_env_string(args.name) if args.name else expanded_cmd

    stdout_assertions: list[TextAssertion] = []
    if args.stdout_contains is not None:
        stdout_assertions.append(
            TextAssertion(op="contains", value=expand_env_string(args.stdout_contains))
        )
    if args.stdout_equals is not None:
        stdout_assertions.append(
            TextAssertion(op="equals", value=expand_env_string(args.stdout_equals))
        )
    if args.stdout_regex is not None:
        stdout_assertions.append(
            TextAssertion(op="regex", value=expand_env_string(args.stdout_regex))
        )

    json_assertions: list[JsonAssertion] = []
    if args.json_path:
        json_path = expand_env_string(args.json_path)

        if args.json_equals is not None:
            json_assertions.append(
                JsonAssertion(
                    path=json_path,
                    op="equals",
                    value=expand_env_string(args.json_equals),
                )
            )
        if args.json_contains is not None:
            json_assertions.append(
                JsonAssertion(
                    path=json_path,
                    op="contains",
                    value=expand_env_string(args.json_contains),
                )
            )
        if args.json_regex is not None:
            json_assertions.append(
                JsonAssertion(
                    path=json_path,
                    op="regex",
                    value=expand_env_string(args.json_regex),
                )
            )
        if args.json_startswith is not None:
            json_assertions.append(
                JsonAssertion(
                    path=json_path,
                    op="startswith",
                    value=expand_env_string(args.json_startswith),
                )
            )

    return CheckSpec(
        name=expanded_name,
        cmd=expanded_cmd,
        parser=args.parser,
        expect_code=args.expect_code,
        stdout_assertions=stdout_assertions,
        json_assertions=json_assertions,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "run":
        parser.error("unsupported command")

    checks: list[CheckSpec] = []
    file_passed_label = "PASS"
    file_failed_label = "FAIL"

    if args.file_path:
        file_checks, labels = load_checks(args.file_path)
        checks.extend(file_checks)
        file_passed_label = labels.get("passed", "PASS")
        file_failed_label = labels.get("failed", "FAIL")

    inline_check = inline_check_from_args(args)
    if inline_check:
        checks.append(inline_check)

    if not checks:
        parser.error("provide --file and/or --cmd")

    passed_label = args.passed_label or file_passed_label
    failed_label = args.failed_label or file_failed_label

    result = run_checks(checks, passed_label=passed_label, failed_label=failed_label)

    chunks: list[str] = []

    if args.output == "text":
        chunks.append(render_output_text(result))
    elif args.output == "json":
        chunks.append(render_output_json(result))

    if args.summary == "text":
        chunks.append(render_summary_text(result))
    elif args.summary == "table":
        chunks.append(render_summary_table(result))
    elif args.summary == "markdown":
        chunks.append(render_summary_markdown(result))

    if chunks:
        sys.stdout.write("\n".join(chunks) + "\n")

    return 0 if result.failed_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())