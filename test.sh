#!/bin/bash

# Test End-To-End

set -euo pipefail

BUILDER_PYTHON="3.12"

# Build test requirements
uv run --python "$BUILDER_PYTHON" src/update.py --environment test

# Build test PREFIX
mkdir -p monobase cache
docker run --rm \
    --hostname monobase-builder \
    --volume "$PWD/src:/opt/r8/monobase" \
    --volume "$PWD/monobase:/srv/r8/monobase" \
    --volume "$PWD/cache:/var/cache/monobase" \
    monobase:latest \
    --environment test \
    "$@"

fail=0
test() {
    op="$1"
    f="$PWD/monobase/$2"
    r=0
    case "$op" in
        -d) [ -d "$f" ] || r=1 ;;
        -f) [ -f "$f" ] || r=1 ;;
        -h) [ -h "$f" ] || r=1 ;;
        -x) [ -x "$f" ] || r=1 ;;
    esac

    if [ "$r" -eq 0 ]; then
        echo "PASS: [ $op /srv/r8/monobase/$2 ]"
    else
        echo "FAIL: [ $op /srv/r8/monobase/$2 ]"
        fail=$((fail+1))
    fi
}

# Test /srv/r8/monobase structure
test -x 'bin/uv'
test -x 'bin/pget'
test -d 'monobase/g00000'
test -f 'monobase/g00000/.done'
test -h 'monobase/g00000/cuda12.4'
test -f 'monobase/g00000/cuda12.4/.done'
test -h 'monobase/g00000/cudnn9-cuda12'
test -f 'monobase/g00000/cudnn9-cuda12/.done'
test -d 'monobase/g00000/ld.so.cache.d'
test -d 'monobase/g00000/python3.12-torch2.4.1-cu124'
test -f 'monobase/g00000/python3.12-torch2.4.1-cu124/.done'

if [ "$fail" -gt 0 ]; then
    exit 1
fi

# Test versions
read -r -d '' SCRIPT << EOF || :
import sys, cog, torch
assert sys.version.startswith('3.12.6'), f'sys.version is not 3.12.6: {sys.version}'
assert cog.__version__ == '0.9.23', f'cog.__version__ is not 0.9.23: {cog.__version__}'
assert torch.__version__ == '2.4.1+cu124', f'torch.__version__ is not 2.4.1+cu124: {torch.__version__}'
print('PASS: Python imports')
EOF

docker run --rm \
    --volume "$PWD/src:/opt/r8/monobase" \
    --volume "$PWD/monobase:/srv/r8/monobase" \
    --env CUDA_VERSION=12.4 \
    --env CUDNN_VERSION=9 \
    --env PYTHON_VERSION=3.12 \
    --env TORCH_VERSION=2.4.1 \
    monobase:latest \
    python -c "$SCRIPT"

echo 'DONE: all tests passed'
