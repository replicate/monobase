#!/bin/bash

# Lint and format

set -euo pipefail

R8_PYTHON_VERSION='3.12'

cd "$(git rev-parse --show-toplevel)"

uv run --python "$R8_PYTHON_VERSION" src/monogen.py

if [[ -z "${CI:-}" ]]; then
    uv tool run ruff check --fix
    uv tool run ruff format
else
    uv tool run ruff check
    uv tool run ruff format --check
fi
uv run --python "$R8_PYTHON_VERSION" --with mypy mypy src
