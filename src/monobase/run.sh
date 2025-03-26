#!/bin/bash

# Run Python modules in monobase

set -euo pipefail

export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-monobase}"
export PATH="$MONOBASE_PREFIX/bin:$PATH"

UV_URL='https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-unknown-linux-gnu.tar.gz'
PGET_URL='https://github.com/replicate/pget/releases/latest/download/pget_Linux_x86_64'

log() {
    echo "$(date --iso-8601=seconds --utc) $*"
}

if [ $# -lt 1 ]; then
    echo "Usage: $(basename "$0") <module> [arg]..."
    exit 1
fi

module="$1"
shift

# Install uv and pget if missing
# Always install latest if module is monobase.build
if [ "$module" == "monobase.build" ] || ! [ -f "$MONOBASE_PREFIX/bin/uv" ] || ! [ -f "$MONOBASE_PREFIX/bin/pget-bin" ]; then
    mkdir -p "$MONOBASE_PREFIX/bin"

    log "Installing uv..."
    curl -fsSL "$UV_URL" | tar -xz --strip-components=1 -C /tmp
    mv /tmp/uv "$MONOBASE_PREFIX/bin"
    "$MONOBASE_PREFIX/bin/uv" --version

    log "Installing pget..."
    curl -fsSL "$PGET_URL" -o /tmp/pget-bin
    chmod +x /tmp/pget-bin
    mv /tmp/pget-bin "$MONOBASE_PREFIX/bin/pget-bin"
    "$MONOBASE_PREFIX/bin/pget-bin" version

    # PGET FUSE wrapper
    cp /opt/r8/monobase/pget "$MONOBASE_PREFIX/bin/pget"

    # Remove venv for pget that didn't work
    if [ -d "$MONOBASE_PREFIX/venv" ]; then
        rm -rf "$MONOBASE_PREFIX/venv"
    fi
fi

if ! [ -d /var/tmp/.venv ]; then
    log "Installing monobase..."
    uv venv /var/tmp/.venv --python='3.13'
    VIRTUAL_ENV=/var/tmp/.venv uv pip install --link-mode=copy "$(find /opt/r8 -name '*.whl' | head -1)"
fi

log "Running $module..."
export PATH="$PATH:/var/tmp/.venv/bin"
exec /var/tmp/.venv/bin/python3 -m "$module" "$@"
