#!/bin/bash

# Lint and format

set -euo pipefail

MONOBASE_PYTHON='3.12'

cd "$(git rev-parse --show-toplevel)"

if [[ -z "${CI:-}" ]]; then
    uv tool run ruff check --fix
    uv tool run ruff format
else
    uv tool run ruff check
    uv tool run ruff format --check
fi
uv run --python "$MONOBASE_PYTHON" --with mypy mypy src
