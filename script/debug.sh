#!/usr/bin/env bash

# Start a debug container with the test environment

set -euo pipefail

MONOBASE_PYTHON='3.13'

cd "$(git rev-parse --show-toplevel)"

# Build test requirements
uv run --python "$MONOBASE_PYTHON" python -m monobase.update --environment test

# Build test PREFIX
mkdir -p build/monobase build/cache

exec docker run --rm -it \
    --hostname debug \
    --user "$(id -u):$(id -g)" \
    --workdir '/opt/r8' \
    --volume "$PWD/src/monobase:/opt/r8/monobase" \
    --volume "$PWD/build/monobase:/srv/r8/monobase" \
    --volume "$PWD/build/cache:/var/cache/monobase" \
    monobase:latest \
    bash -l
