#!/bin/bash

# Update production generations

set -euo pipefail

PYTHON_VERSION='3.12'

cd "$(git rev-parse --show-toplevel)"
uv run --python "$PYTHON_VERSION" src/update.py --environment prod "$@"
