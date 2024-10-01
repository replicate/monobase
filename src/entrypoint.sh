#!/bin/bash

# Entrypoint script

set -euo pipefail

PREFIX='/usr/local'
BUILDER_PYTHON='3.12'
DONE_FILE='/srv/r8/monobase/.done'

UV_URL='https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-unknown-linux-gnu.tar.gz'
PGET_URL='https://github.com/replicate/pget/releases/latest/download/pget_Linux_x86_64'

log() {
    echo "$(date --iso-8601=seconds --utc) $*"
}

builder() {
    if [ -n "${MONOBASE_CLEAN:-}" ]; then
        log "Cleaning up $PREFIX..."
        rm -rf "${PREFIX:?}"/{bin,cuda,monobase,uv}
        rm -f "$DONE_FILE"
    fi

    if [ -f "$DONE_FILE" ]; then
        log "Monobase ready, skipping build"
    else
        mkdir -p "$PREFIX/bin"

        # Always install latest uv and pget first

        log "Installing uv..."
        curl -fsSL "$UV_URL" | tar -xz --strip-components=1 -C "$PREFIX/bin"
        "$PREFIX/bin/uv" --version

        log "Installing pget..."
        curl -fsSL -o "$PREFIX/bin/pget" "$PGET_URL"
        chmod +x "$PREFIX/bin/pget"
        "$PREFIX/bin/pget" version

        log "Running builder..."
        uv run --python "$BUILDER_PYTHON" /srv/r8/monobase/build.py "$@"

        touch "$DONE_FILE"
    fi

    # Sleep inside K8S to keep pod alive
    if [ -n "${KUBERNETES_SERVICE_HOST:-}" ]; then
        sleep 86400
    fi
}

model() {
    # shellcheck disable=SC1091
    . /srv/r8/monobase/env.sh
    exec "$@"
}

case $HOSTNAME in
    monobase-*) builder "$@" ;;
    *) model "$@" ;;
esac
