#!/bin/bash

# Lint and format

set -euo pipefail

MONOBASE_PYTHON='3.12'

cd "$(git rev-parse --show-toplevel)"
uv tool run ruff check --fix
uv tool run ruff format
uv run --python "$MONOBASE_PYTHON" --with mypy mypy src
