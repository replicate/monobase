#!/bin/bash

# Entrypoint script

set -euo pipefail

export PATH="$MONOBASE_PREFIX/bin:$PATH"

log() {
    echo "$(date --iso-8601=seconds --utc) $*"
}

model() {
    # shellcheck disable=SC1091
    . /opt/r8/monobase/env.sh
    exec "$@"
}

case $HOSTNAME in
    monobase-*) /opt/r8/monobase/build.sh "$@" ;;
    *) model "$@" ;;
esac
