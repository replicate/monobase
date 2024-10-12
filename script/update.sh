#!/bin/bash

# Update production generations

set -euo pipefail

MONOBASE_PYTHON='3.12'

cd "$(git rev-parse --show-toplevel)"
uv run --python "$MONOBASE_PYTHON" src/update.py --environment prod "$@"
