#!/bin/bash

# Entrypoint script

set -euo pipefail

export PATH="$MONOBASE_PREFIX/bin:$PATH"
export PYTHONPATH='/opt/r8'

log() {
    echo "$(date --iso-8601=seconds --utc) $*"
}

model() {
    # shellcheck disable=SC1091
    . /opt/r8/monobase/env.sh
    exec "$@"
}

case $HOSTNAME in
    debug) exec bash -l ;;
    monobase-*) /opt/r8/monobase/build.sh "$@" ;;
    *) model "$@" ;;
esac
