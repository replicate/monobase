#!/bin/bash

# Update production generations

set -euo pipefail

uv run --python 3.12 src/update.py --environment prod "$@"
