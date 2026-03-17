# sanityctl

A lightweight command-line tool for running simple sanity checks against shell commands.

`sanityctl` is designed for situations where you want a small, understandable, low-ceremony way to validate command behavior without building a full testing framework.

It supports:

- checks loaded from YAML files
- one-off inline checks from the CLI
- plain text assertions
- JSON assertions
- human-readable summaries
- machine-readable JSON output

---

## Table of contents

1. Overview
2. Why this project exists
3. Repository layout
4. Core concepts
5. Installation
6. Quick start
7. CLI reference
8. YAML configuration format
9. Assertion reference
10. Output formats
11. Exit codes
12. Makefile targets
13. Development workflow
14. Building a standalone binary

---

## Overview

`sanityctl` executes shell commands and validates their results.

A check can validate:

- process exit code
- stdout as plain text
- stdout parsed as JSON

This makes it useful for:

- smoke checks after deployments
- validating CLI tools
- checking wrappers around APIs
- quick CI/CD health checks
- maintaining a small set of operational sanity checks in one file

The goal is not to replace full test frameworks. The goal is to make simple checks easy to define, easy to run, and easy to understand six months later.

---

## Why this project exists

There is a common gap between:

- "I only need to run a command and confirm a few expectations"
- and
- "I do not want to build a full pytest suite, bash harness, or custom framework for this"

Examples:

- verify that `python --version` still works
- verify that a command prints a known substring
- verify that a command returns JSON with `status=ok`
- verify that a version starts with a known prefix
- fail a pipeline if a smoke check no longer passes

`sanityctl` is intended to stay small and understandable.

---

## Example installation

### Pinned version    

```bash  
set -euo pipefail  
arch="$(uname -m)"  
case "$arch" in  
    x86_64|amd64) asset="sanityctl-linux-amd64" ;;  
    aarch64|arm64) asset="sanityctl-linux-arm64" ;;  
    *) echo "Unsupported architecture: $arch" >&2; exit 1 ;;  
esac  
version="X.Y.Z"  
base="https://github.com/rafalmasiarek/py-sanityctl/releases/download/v${version}"  
curl -fsSL -o /tmp/"$asset" "$base/$asset"  
curl -fsSL -o /tmp/SHA256SUMS.txt "$base/SHA256SUMS.txt"  
( cd /tmp && grep " $asset\$" SHA256SUMS.txt | sha256sum -c - )  
sudo install -m 0755 /tmp/"$asset" /usr/local/bin/sanityctl  
sanityctl --help
```  
  
### Latest rolling release  
  
Use this when you want the newest available binary.  
  
```bash  
set -euo pipefail  
arch="$(uname -m)"  
case "$arch" in  
    x86_64|amd64) asset="sanityctl-linux-amd64" ;;  
    aarch64|arm64) asset="sanityctl-linux-arm64" ;;  
    *) echo "Unsupported architecture: $arch" >&2; exit 1 ;;  
esac  
base="https://github.com/rafalmasiarek/py-sanityctl/releases/download/latest"  
curl -fsSL -o /tmp/"$asset" "$base/$asset"  
curl -fsSL -o /tmp/SHA256SUMS.txt "$base/SHA256SUMS.txt"  
( cd /tmp && grep " $asset\$" SHA256SUMS.txt | sha256sum -c - )  
sudo install -m 0755 /tmp/"$asset" /usr/local/bin/sanityctl  
sanityctl --help
```    
  
### Recommendation  
  
- Use `vX.Y.Z` for stable CI/CD pipelines  
- Use `latest` for convenience and fast-moving internal tooling

## Repository layout

```text
.
├── Makefile
├── pyproject.toml
├── examples/
│   └── checks.yaml
├── src/
│   └── sanityctl/
│       ├── __init__.py
│       ├── assertions.py
│       ├── cli.py
│       ├── config.py
│       ├── models.py
│       ├── reporters.py
│       ├── runner.py
│       └── utils.py
└── tests/
    └── test_smoke.py
```

### File guide

#### `src/sanityctl/cli.py`
Defines the CLI.

Responsibilities:

- parse arguments
- define commands and options
- load checks from YAML
- build one inline check from CLI arguments
- choose output and summary format
- return correct process exit code

Read this first when you want to remember how the tool is used.

#### `src/sanityctl/config.py`
Loads YAML configuration into internal models.

Responsibilities:

- read YAML file
- parse `checks`
- parse report labels
- create `CheckSpec`, `TextAssertion`, and `JsonAssertion`

Read this when you want to understand the config format.

#### `src/sanityctl/models.py`
Defines the core data model.

Key classes:

- `CheckSpec` — one check definition
- `CheckResult` — one executed check result
- `RunResult` — combined result of all checks

Read this when you want to understand what the system considers a "check" and a "result".

#### `src/sanityctl/assertions.py`
Implements assertion logic.

Responsibilities:

- text assertions
- JSON assertions
- JSON parsing helper

Read this when you want to add new assertion operators.

#### `src/sanityctl/runner.py`
Runs checks.

Responsibilities:

- execute shell commands
- collect stdout/stderr
- check exit code
- apply assertions
- build structured results

Read this when you want to change runtime behavior.

#### `src/sanityctl/reporters.py`
Renders output.

Responsibilities:

- text output
- JSON output
- summary output
- table summary
- markdown summary

Read this when you want to change presentation.

#### `src/sanityctl/utils.py`
Contains helper logic.

Currently includes JSON path resolution.

#### `examples/checks.yaml`
Example configuration file showing supported concepts.

#### `tests/test_smoke.py`
Minimal smoke test for the execution pipeline.

#### `Makefile`
Convenience targets for install, test, examples, and building the binary.

---

## Core concepts

### Check
A single command execution with expectations.

A check has:

- a name
- a shell command
- an expected exit code
- optional text assertions
- optional JSON assertions
- optional parser mode

### Run
A collection of one or more checks executed together.

### Parser mode

Two parser modes are supported:

- `text` — stdout is treated as plain text
- `json` — stdout is parsed as JSON before JSON assertions are applied

### Assertions

Two assertion families exist:

- text assertions against raw stdout
- JSON assertions against a value selected by a JSON path

---

## Installation

### Local development install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -e .
```

If you need test tooling too:

```bash
pip install pytest
```

### Run from virtual environment

```bash
.venv/bin/sanityctl --help
```

or after activation:

```bash
sanityctl --help
```

---

## Quick start

### Smallest useful inline check

```bash
sanityctl run \
  --cmd "printf 'hello'" \
  --stdout-contains hello \
  --summary
```

### Run checks from YAML

```bash
sanityctl run -f examples/checks.yaml --summary table
```

### Get machine-readable output

```bash
sanityctl run -f examples/checks.yaml --output json
```

### Run YAML checks and append one extra inline check

```bash
sanityctl run \
  -f examples/checks.yaml \
  --name "extra runtime check" \
  --cmd "printf 'runtime-ok'" \
  --stdout-contains runtime-ok \
  --summary table
```

---

## CLI reference

The top-level CLI currently exposes one subcommand:

```bash
sanityctl run
```

### General form

```bash
sanityctl run [options]
```

### Input options

#### `-f, --file PATH`
Load checks from a YAML file.

Example:

```bash
sanityctl run -f examples/checks.yaml
```

#### `--name TEXT`
Display name for the inline check created by `--cmd`.

If omitted, the command text itself is used as the name.

Example:

```bash
sanityctl run --name "hello check" --cmd "printf 'hello'" --stdout-contains hello
```

#### `--cmd COMMAND`
Define one inline check directly from the CLI.

Example:

```bash
sanityctl run --cmd "printf 'hello'" --stdout-contains hello
```

---

### Inline check behavior options

#### `--expect-code N`
Expected process exit code for the inline check.

Default:

```text
0
```

Example:

```bash
sanityctl run \
  --cmd "python -c 'import sys; sys.exit(7)'" \
  --expect-code 7
```

#### `--parser {text,json}`
Controls how stdout from the inline command is interpreted.

- `text` — plain text stdout
- `json` — parse stdout as JSON

Default:

```text
text
```

Example:

```bash
sanityctl run \
  --cmd "python -c 'import json; print(json.dumps({\"status\":\"ok\"}))'" \
  --parser json \
  --json-path status \
  --json-equals ok
```

---

### Inline text assertion options

These apply only to the inline check.

#### `--stdout-contains TEXT`
Pass if stdout contains a substring.

Example:

```bash
sanityctl run --cmd "printf 'hello world'" --stdout-contains hello
```

#### `--stdout-equals TEXT`
Pass if stdout exactly equals the given value.

Example:

```bash
sanityctl run --cmd "printf 'OK'" --stdout-equals OK
```

#### `--stdout-regex REGEX`
Pass if stdout matches a regular expression.

Example:

```bash
sanityctl run \
  --cmd "python -c 'print(\"version=1.2.3\")'" \
  --stdout-regex '^version=\d+\.\d+\.\d+$'
```

---

### Inline JSON assertion options

These usually require:

- `--parser json`
- `--json-path ...`

#### `--json-path PATH`
Select a value inside parsed JSON.

Supported examples:

```text
status
service.name
items[0]
items[0].name
```

#### `--json-equals VALUE`
Pass if the selected JSON value equals the expected value.

Example:

```bash
sanityctl run \
  --cmd "python -c 'import json; print(json.dumps({\"status\":\"ok\"}))'" \
  --parser json \
  --json-path status \
  --json-equals ok
```

#### `--json-contains VALUE`
Pass if the selected JSON value contains the expected value after conversion to string.

Example:

```bash
sanityctl run \
  --cmd "python -c 'import json; print(json.dumps({\"version\":\"1.2.3\"}))'" \
  --parser json \
  --json-path version \
  --json-contains 1.2
```

#### `--json-regex REGEX`
Pass if the selected JSON value matches a regular expression after conversion to string.

Example:

```bash
sanityctl run \
  --cmd "python -c 'import json; print(json.dumps({\"version\":\"1.2.3\"}))'" \
  --parser json \
  --json-path version \
  --json-regex '^1\.2\.[0-9]+$'
```

#### `--json-startswith PREFIX`
Pass if the selected JSON value starts with a prefix after conversion to string.

Example:

```bash
sanityctl run \
  --cmd "python -c 'import json; print(json.dumps({\"version\":\"1.2.3\"}))'" \
  --parser json \
  --json-path version \
  --json-startswith 1.2
```

---

### Output options

#### `--output {text,json,none}`
Controls the main per-check output block.

Values:

- `text` — one line per check
- `json` — machine-readable JSON document
- `none` — suppress per-check output

Default:

```text
text
```

Examples:

```bash
sanityctl run -f examples/checks.yaml --output text
sanityctl run -f examples/checks.yaml --output json
sanityctl run -f examples/checks.yaml --output none --summary table
```

#### `--summary [text|table|markdown]`
Append a summary block.

If used without a value, it defaults to `text`.

Examples:

```bash
sanityctl run -f examples/checks.yaml --summary
sanityctl run -f examples/checks.yaml --summary table
sanityctl run -f examples/checks.yaml --summary markdown
```

#### `--passed-label TEXT`
Override the label shown for passing checks.

Example:

```bash
sanityctl run -f examples/checks.yaml --passed-label OK --failed-label BAD
```

#### `--failed-label TEXT`
Override the label shown for failing checks.

---

## YAML configuration format

A YAML file may contain:

- `report`
- `checks`

### Full example

```yaml
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

  - name: json hello
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
          value: "1.2"

  - name: failing example
    cmd: python -c 'import sys; sys.exit(7)'
    expect:
      code: 0
```

### Top-level `report` section

Used to configure presentation defaults.

Example:

```yaml
report:
  status_labels:
    passed: PASS
    failed: FAIL
```

### `checks` section

A list of checks.

Each check may define:

- `name`
- `cmd`
- `parser`
- `timeout`
- `env`
- `workdir`
- `expect`

### Minimal text check

```yaml
checks:
  - name: hello check
    cmd: printf 'hello'
    expect:
      code: 0
      stdout:
        - op: contains
          value: "hell"
```

### Minimal JSON check

```yaml
checks:
  - name: status check
    cmd: python -c 'import json; print(json.dumps({"status":"ok"}))'
    parser: json
    expect:
      code: 0
      json:
        - path: status
          op: equals
          value: ok
```

### Check fields

#### `name`
Human-readable check name.

#### `cmd`
Shell command to execute.

#### `parser`
Optional. One of:

- `text`
- `json`

Default is `text`.

#### `timeout`
Optional command timeout.

#### `env`
Optional environment variables.

Example:

```yaml
env:
  APP_ENV: prod
  FEATURE_FLAG: true
```

#### `workdir`
Optional working directory for command execution.

#### `expect.code`
Expected process exit code.

#### `expect.stdout`
List of text assertions.

#### `expect.json`
List of JSON assertions.

---

## Assertion reference

### Text assertion operators

#### `contains`
Pass if substring exists in stdout.

```yaml
stdout:
  - op: contains
    value: "Python"
```

#### `equals`
Pass if stdout exactly equals expected value.

```yaml
stdout:
  - op: equals
    value: "OK"
```

#### `regex`
Pass if stdout matches regex.

```yaml
stdout:
  - op: regex
    value: '^version=\d+\.\d+\.\d+$'
```

---

### JSON assertion operators

#### `exists`
Pass if the JSON path resolves successfully.

```yaml
json:
  - path: status
    op: exists
```

#### `equals`
Pass if JSON value equals expected value.

```yaml
json:
  - path: status
    op: equals
    value: ok
```

#### `contains`
Pass if expected text is found inside the JSON value after string conversion.

```yaml
json:
  - path: version
    op: contains
    value: "1.2"
```

#### `startswith`
Pass if JSON value starts with expected prefix after string conversion.

```yaml
json:
  - path: version
    op: startswith
    value: "1.2"
```

#### `regex`
Pass if JSON value matches regex after string conversion.

```yaml
json:
  - path: version
    op: regex
    value: '^1\.2\.[0-9]+$'
```

---

## JSON path reference

Current path syntax supports dotted object access and list indexing.

Examples:

```text
status
service.name
items[0]
items[0].name
data.results[2].id
```

If a path cannot be resolved, the assertion fails.

---

## Output formats

### `--output text`
Example:

```text
PASS python version
PASS json hello
FAIL failing example
```

### `--output json`
Example structure:

```json
{
  "summary": {
    "total": 3,
    "passed": 2,
    "failed": 1,
    "status": "FAIL"
  },
  "checks": [
    {
      "name": "python version",
      "passed": true,
      "status": "PASS",
      "exit_code": 0,
      "duration_ms": 3,
      "failures": []
    }
  ]
}
```

### `--summary text`
Example:

```text
3 checks, 2 passed, 1 failed
```

### `--summary table`
Example:

```text
+-----------------+--------+-----------+-------------+
| Check           | Status | Exit Code | Duration ms |
+-----------------+--------+-----------+-------------+
| python version  | PASS   | 0         | 3           |
| json hello      | PASS   | 0         | 25          |
| failing example | FAIL   | 7         | 17          |
+-----------------+--------+-----------+-------------+
```

### `--summary markdown`
Example:

| Check | Status | Exit Code | Duration ms |
|---|---|---:|---:|
| python version | PASS | 0 | 3 |
| json hello | PASS | 0 | 25 |
| failing example | FAIL | 7 | 17 |

---

## Exit codes

`sanityctl` returns:

- `0` when all checks pass
- `1` when at least one check fails

This makes it useful in automation and CI pipelines.

Important implication:

- `make example` may fail if the example file intentionally includes a failing check
- this is expected behavior, not a bug

---

## Makefile targets

Current targets are intended to support day-to-day development and quick rediscovery.

### `make install`
Create local virtual environment and install the project.

### `make reinstall`
Delete `.venv` and recreate it.

### `make example`
Run the example YAML file.

This may fail intentionally if the example config includes a failing check.

### `make example-pass`
Run a passing inline example.

Useful when you want a fast green-path demonstration.

### `make example-fail`
Run a failing inline example.

Useful when you want to see failure behavior and exit status.

### `make inline`
Run a small inline text assertion example.

### `make test`
Run smoke tests.

### `make build`
Build standalone binary with PyInstaller.

### `make rebuild`
Clean build artifacts and rebuild binary.

### `make run-bin`
Run the built binary.

### `make clean`
Remove caches and build artifacts.

### `make distclean`
Remove caches, build artifacts, and the virtual environment.

---

## Development workflow

A practical local workflow:

### First setup

```bash
make install
```

### Run help

```bash
.venv/bin/sanityctl --help
.venv/bin/sanityctl run --help
```

### Run examples

```bash
make example
make example-pass
make example-fail
```

### Run tests

```bash
make test
```

### Build binary

```bash
make build
./dist/sanityctl --help
```

---

## Building a standalone binary

### Build

```bash
make build
```

Expected artifact:

```text
dist/sanityctl
```

### Run

```bash
./dist/sanityctl --help
./dist/sanityctl run --name hello --cmd "printf 'hello'" --stdout-contains hello --summary
```

---

## Example command cookbook

### Check that Python exists

```bash
sanityctl run \
  --name "python version" \
  --cmd "python --version" \
  --stdout-contains Python \
  --summary
```

### Check that JSON status is ok

```bash
sanityctl run \
  --name "status check" \
  --cmd "python -c 'import json; print(json.dumps({\"status\":\"ok\"}))'" \
  --parser json \
  --json-path status \
  --json-equals ok \
  --summary
```

### Check that version starts with 1.2

```bash
sanityctl run \
  --name "version prefix" \
  --cmd "python -c 'import json; print(json.dumps({\"version\":\"1.2.3\"}))'" \
  --parser json \
  --json-path version \
  --json-startswith 1.2
```

### Only print summary

```bash
sanityctl run \
  -f examples/checks.yaml \
  --output none \
  --summary table
```

### Produce JSON for automation

```bash
sanityctl run \
  -f examples/checks.yaml \
  --output json
```

---

## Mental model to remember after six months

If you come back to this repository later, remember this:

- `cli.py` = how users talk to the tool
- `config.py` = how YAML becomes Python objects
- `models.py` = what the important objects are
- `runner.py` = where commands are executed
- `assertions.py` = how checks pass or fail
- `reporters.py` = how results are shown
- `Makefile` = common commands you will actually run

And the main user flows are just these:

```bash
make install
make example
make test
make build
./dist/sanityctl --help
```
