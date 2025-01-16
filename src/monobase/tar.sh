#!/bin/bash

set -euo pipefail

# Create a reproducible tarball

if [ $# -le 2 ]; then
    echo "Usage $(basename "$0") <TARBALL> <ROOT> [FILE]..."
    exit 1
fi

export LC_ALL=C
export TZ=UTC

tarball="$1"
root="$2"
shift 2

exec tar \
    --sort=name \
    --format=posix \
    --pax-option=exthdr.name=%d/PaxHeaders/%f \
    --pax-option=delete=atime,delete=ctime,delete=btime,delete=mtime \
    --mtime=0 \
    --numeric-owner \
    --owner=0 \
    --group=0 \
    --mode=go+u,go-w \
    --zstd \
    -cvf "$tarball" \
    -C "$root" \
    "$@"
