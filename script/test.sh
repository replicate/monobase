#!/bin/bash

# Test End-To-End

set -euo pipefail

MONOBASE_PYTHON='3.13'

cd "$(git rev-parse --show-toplevel)"

# Build test requirements
uv run --python "$MONOBASE_PYTHON" python -m monobase.update --environment test

# Build test PREFIX
mkdir -p build/monobase build/cache
docker run --rm \
    --hostname monobase-builder \
    --user "$(id -u):$(id -g)" \
    --volume "$PWD/src/monobase:/opt/r8/monobase" \
    --volume "$PWD/build/monobase:/srv/r8/monobase" \
    --volume "$PWD/build/cache:/var/cache/monobase" \
    monobase:latest \
    --environment test \
    --skip-cuda \
    --cog-versions \
    0.11.3 \
    https://github.com/replicate/cog/archive/00b98bc90bb784102243b7aec41ad1cbffaefece.zip \
    --default-cog-version 0.11.3 \
    "$@"

fail=0
test() {
    op="$1"
    f="$PWD/build/monobase/$2"
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
test -h 'cog/latest'
test -f 'cog/latest/.done'
test -h 'cog/latest/default-python3.12'
test -h 'monobase/latest'
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

read -r -d '' SCRIPT << EOF || :
import sys, cog, torch
assert sys.version.startswith('3.12.7'), f'sys.version is not 3.12.7: {sys.version}'
assert cog.__file__.startswith('/srv/r8/monobase/cog'), f'cog is not pre-installed: {cog.__file__}'
assert cog.__version__ == '0.11.3', f'cog.__version__ is not 0.11.3: {cog.__version__}'
assert torch.__version__ == '2.4.1+cu124', f'torch.__version__ is not 2.4.1+cu124: {torch.__version__}'
print('PASS: venv versions')
EOF

docker run --rm \
    --volume "$PWD/src/monobase:/opt/r8/monobase" \
    --volume "$PWD/build/monobase:/srv/r8/monobase" \
    --env R8_CUDA_VERSION=12.4 \
    --env R8_CUDNN_VERSION=9 \
    --env R8_PYTHON_VERSION=3.12 \
    --env R8_TORCH_VERSION=2.4.1 \
    monobase:latest \
    python -c "$SCRIPT"

read -r -d '' SCRIPT << EOF || :
import cog
assert cog.__file__.startswith('/srv/r8/monobase/cog'), f'cog is not pre-installed: {cog.__file__}'
assert cog.__version__ == '0.11.3', f'cog.__version__ is not 0.11.3: {cog.__version__}'
print('PASS: Pre-installed cog==0.11.3')
EOF
docker run --rm \
    --volume "$PWD/src/monobase:/opt/r8/monobase" \
    --volume "$PWD/build/monobase:/srv/r8/monobase" \
    --env R8_COG_VERSION=0.11.3 \
    --env R8_CUDA_VERSION=12.4 \
    --env R8_CUDNN_VERSION=9 \
    --env R8_PYTHON_VERSION=3.12 \
    --env R8_TORCH_VERSION=2.4.1 \
    monobase:latest \
    python -c "$SCRIPT"

read -r -d '' SCRIPT << EOF || :
import cog
assert cog.__file__.startswith('/srv/r8/monobase/cog'), f'cog is not pre-installed: {cog.__file__}'
assert cog.__version__ == '0.11.2.dev71+g00b98bc90b', f'cog.__version__ is not 0.11.2.dev71+g00b98bc90b: {cog.__version__}'
print('PASS: Pre-installed cog==cog @ https://...')
EOF
docker run --rm \
    --volume "$PWD/src/monobase:/opt/r8/monobase" \
    --volume "$PWD/build/monobase:/srv/r8/monobase" \
    --env R8_COG_VERSION=https://github.com/replicate/cog/archive/00b98bc90bb784102243b7aec41ad1cbffaefece.zip \
    --env R8_CUDA_VERSION=12.4 \
    --env R8_CUDNN_VERSION=9 \
    --env R8_PYTHON_VERSION=3.12 \
    --env R8_TORCH_VERSION=2.4.1 \
    monobase:latest \
    python -c "$SCRIPT"

read -r -d '' SCRIPT << EOF || :
import cog
assert cog.__file__.startswith('/root/cog'), f'cog is not installed on the fly: {cog.__file__}'
assert cog.__version__ == '0.9.0', f'cog.__version__ is not 0.9.0: {cog.__version__}'
print('PASS: On-demand cog==0.9.0')
EOF
docker run --rm \
    --volume "$PWD/src/monobase:/opt/r8/monobase" \
    --volume "$PWD/build/monobase:/srv/r8/monobase" \
    --env R8_COG_VERSION=0.9.0 \
    --env R8_CUDA_VERSION=12.4 \
    --env R8_CUDNN_VERSION=9 \
    --env R8_PYTHON_VERSION=3.12 \
    --env R8_TORCH_VERSION=2.4.1 \
    monobase:latest \
    python -c "$SCRIPT"

read -r -d '' SCRIPT << EOF || :
import cog
assert cog.__file__.startswith('/root/cog'), f'cog is not installed on the fly: {cog.__file__}'
assert cog.__version__ == '0.11.4.dev77+g8ea4663247', f'cog.__version__ is not 0.11.4.dev77+g8ea4663247: {cog.__version__}'
print('PASS: On-demand cog==cog @ https://...')
EOF
docker run --rm \
    --volume "$PWD/src/monobase:/opt/r8/monobase" \
    --volume "$PWD/build/monobase:/srv/r8/monobase" \
    --env R8_COG_VERSION=https://github.com/replicate/cog/archive/8ea466324738f3143954ec5be3211051659a20da.zip \
    --env R8_CUDA_VERSION=12.4 \
    --env R8_CUDNN_VERSION=9 \
    --env R8_PYTHON_VERSION=3.12 \
    --env R8_TORCH_VERSION=2.4.1 \
    monobase:latest \
    python -c "$SCRIPT"

# NCCL
read -r -d '' SCRIPT << EOF || :
import ctypes
ctypes.CDLL('libnccl.so.2')
print('PASS: NCCL')
EOF
docker run --rm \
    --volume "$PWD/src/monobase:/opt/r8/monobase" \
    --volume "$PWD/build/monobase:/srv/r8/monobase" \
    --env R8_CUDA_VERSION=12.4 \
    --env R8_CUDNN_VERSION=9 \
    --env R8_PYTHON_VERSION=3.12 \
    --env R8_TORCH_VERSION=2.4.1 \
    monobase:latest \
    python -c "$SCRIPT"

echo 'DONE: all tests passed'
