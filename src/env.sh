#!/bin/sh

# Source this in entry point

if [ -n "${MONOBASE_LATEST:-}" ]; then
    gdir="$(find /usr/local/monobase -mindepth 1 -maxdepth 1 -type d -name 'g*')"
    MONOBASE_GEN_ID="$(basename "$gdir" | sed 's/^g0\{0,4\}//')"

    CUDA_VERSION="$(basename "$(find "$gdir" -mindepth 1 -maxdepth 1 -type l -name 'cuda*')" | sed 's/^cuda//')"
    CUDNN_VERSION="$(basename "$(find "$gdir" -mindepth 1 -maxdepth 1 -type l -name 'cudnn*')" | sed 's/^cudnn\([^-]*\)-cuda.*$/\1/')"

    venv="$(find "$gdir" -mindepth 1 -maxdepth 1 -type d -name 'python*-torch*-cu*')"
    PYTHON_VERSION="$(basename "$venv" | sed 's/python\([^-]*\)-torch[^-]*-cu[^-]*/\1/')"
    TORCH_VERSION="$(basename "$venv" | sed 's/python[^-]*-torch\([^-]*\)-cu[^-]*/\1/')"

    echo "MONOBASE_GEN_ID=$MONOBASE_GEN_ID"
    echo "CUDA_VERSION=$CUDA_VERSION"
    echo "CUDNN_VERSION=$CUDNN_VERSION"
    echo "PYTHON_VERSION=$PYTHON_VERSION"
    echo "TORCH_VERSION=$TORCH_VERSION"

    export MONOBASE_GEN_ID
    export CUDA_VERSION
    export CUDNN_VERSION
    export PYTHON_VERSION
    export TORCH_VERSION
fi

if [ -z "${MONOBASE_GEN_ID:-}" ]; then
    gdir="$(find /usr/local/monobase -mindepth 2 -maxdepth 2 -name .done -type f -exec dirname {} \; | sort | tail -n 1)"
    MONOBASE_GEN_ID="$(basename "$gdir" | sed 's/^g0\{0,4\}//')"
    echo "MONOBASE_GEN_ID not set, using latest $MONOBASE_GEN_ID"
fi

if [ -z "${CUDA_VERSION:-}" ]; then
    echo "CUDA_VERSION not set"
    return 1
fi

if [ -z "${CUDNN_VERSION:-}" ]; then
    echo "CUDNN_VERSION not set"
    return 1
fi

if [ -z "${PYTHON_VERSION:-}" ]; then
    echo "PYTHON_VERSION not set"
    return 1
fi

if [ -z "${TORCH_VERSION:-}" ]; then
    echo "TORCH_VERSION not set"
    return 1
fi

MONOBASE_PATH="/usr/local/monobase/$(printf 'g%05d' "$MONOBASE_GEN_ID")"
CUDA_PATH="$MONOBASE_PATH/cuda$CUDA_VERSION"
CUDA_MAJOR="$(echo "$CUDA_VERSION" | sed 's/\..\+//')"
CUDA_SUFFIX="$(echo "$CUDA_VERSION" | sed 's/\.//')"
CUDNN_PATH="$MONOBASE_PATH/cudnn$CUDNN_VERSION-cuda${CUDA_MAJOR}"
export VIRTUAL_ENV="$MONOBASE_PATH/python$PYTHON_VERSION-torch$TORCH_VERSION-cu$CUDA_SUFFIX"

if ! [ -d "$CUDA_PATH" ]; then
    echo "CUDA $CUDA_VERSION not installed"
    return 1
fi

if ! [ -d "$CUDNN_PATH" ]; then
    echo "CuDNN $CUDNN_VERSION not installed"
    return 1
fi

if ! [ -d "$VIRTUAL_ENV" ]; then
    echo "Virtual environment $VIRTUAL_ENV not installed"
    return 1
fi

export PATH="$VIRTUAL_ENV/bin:$CUDA_PATH/bin${PATH:+:${PATH}}"
export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:$CUDA_PATH/lib64:$CUDNN_PATH/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
export LIBRARY_PATH="$CUDA_PATH/lib64/stubs"

LD_CACHE_PATH="$MONOBASE_PATH/ld.so.cache.d/cuda$CUDA_VERSION-cudnn$CUDNN_VERSION-python$PYTHON_VERSION"
cp -f "$LD_CACHE_PATH" /etc/ld.so.cache
