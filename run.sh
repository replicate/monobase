#!/bin/bash

set -euo pipefail

base_dir="$(git rev-parse --show-toplevel)"

docker run -it --rm \
    --volume "$base_dir/build:/usr/local" \
    --env UV_CACHE_DIR=/usr/local/uv/cache \
    --env UV_PYTHON_INSTALL_DIR=/usr/local/uv/python \
    --env UV_TOOL_BIN_DIR=/usr/local/bin \
    --env UV_TOOL_DIR=/usr/local/uv/tools \
    --env UV_COMPILE_BYTECODE=true \
    --env UV_LINK_MODE=hardlink \
    --env UV_PYTHON_PREFERENCE=only-managed \
    --entrypoint /bin/bash \
    monobase:build
