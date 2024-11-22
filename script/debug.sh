#!/usr/bin/env bash

# Start a debug container with the test environment

set -euo pipefail

MONOBASE_PYTHON='3.13'

cd "$(git rev-parse --show-toplevel)"

# Build test requirements
uv run --python "${MONOBASE_PYTHON}" python -m monobase.update --environment test

# Build test PREFIX
mkdir -p build/monobase build/cache

: "${DEBUG_USER:="$(id -u):$(id -g)"}"
: "${DEBUG_DIR:="/opt/r8"}"

set -x
exec docker run --rm -it \
    --hostname debug \
    --user "${DEBUG_USER}" \
    --workdir "${DEBUG_DIR}" \
    --volume "${PWD}/src/monobase:/opt/r8/monobase" \
    --volume "${PWD}/build/monobase:/srv/r8/monobase" \
    --volume "${PWD}/build/cache:/var/cache/monobase" \
    --env R8_CUDA_VERSION="${R8_CUDA_VERSION:-"12.4"}" \
    --env R8_CUDNN_VERSION="${R8_CUDNN_VERSION:-"9"}" \
    --env R8_PYTHON_VERSION="${R8_PYTHON_VERSION:-"3.12"}" \
    --env R8_TORCH_VERSION="${R8_TORCH_VERSION:-"2.4.1"}" \
    "${DEBUG_IMAGE:-"monobase:latest"}" \
    bash -l
