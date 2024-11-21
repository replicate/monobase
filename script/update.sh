#!/bin/bash

# Update production generations

set -euo pipefail

MONOBASE_PYTHON='3.13'

cd "$(git rev-parse --show-toplevel)"
uv run --python "$MONOBASE_PYTHON" python -m monobase.update --environment prod "$@"
