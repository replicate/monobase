#!/bin/bash

# Entrypoint script

set -euo pipefail

MONOBASE_PYTHON='3.12'
DONE_FILE='/opt/r8/monobase/.done'

UV_URL='https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-unknown-linux-gnu.tar.gz'
PGET_URL='https://github.com/replicate/pget/releases/latest/download/pget_Linux_x86_64'

log() {
    echo "$(date --iso-8601=seconds --utc) $*"
}

builder() {
    mkdir -p "$MONOBASE_PREFIX/bin"

    # Always install latest uv and pget first

    log "Installing uv..."
    curl -fsSL "$UV_URL" | tar -xz --strip-components=1 -C "$MONOBASE_PREFIX/bin"
    "$MONOBASE_PREFIX/bin/uv" --version

    log "Installing pget..."
    curl -fsSL -o "$MONOBASE_PREFIX/bin/pget-bin" "$PGET_URL"
    chmod +x "$MONOBASE_PREFIX/bin/pget-bin"
    "$MONOBASE_PREFIX/bin/pget-bin" version

    # PGET FUSE wrapper
    cp /opt/r8/monobase/pget "$MONOBASE_PREFIX/bin/pget"

    log "Running builder..."
    uv run --python "$MONOBASE_PYTHON" /opt/r8/monobase/build.py "$@"

    # Inside K8S
    # Write done file to signal pod ready
    # Sleep keep pod alive
    if [ -n "${KUBERNETES_SERVICE_HOST:-}" ]; then
        touch "$DONE_FILE"
        sleep 86400
    fi
}

export PATH="$MONOBASE_PREFIX/bin:$PATH"

model() {
    # shellcheck disable=SC1091
    . /opt/r8/monobase/env.sh
    exec "$@"
}

case $HOSTNAME in
    monobase-*) builder "$@" ;;
    *) model "$@" ;;
esac
