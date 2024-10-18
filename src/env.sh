#!/bin/sh

# Source this in entry point

########################################

# Required environment variables

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

########################################

# Cog

if [ -z "${COG_VERSION:-}" ]; then
    COG_PATH="$MONOBASE_PREFIX/cog/latest/default-python$PYTHON_VERSION"
    if [ ! -d "$COG_PATH" ]; then
        echo "Cog $COG_PATH does not exist"
        return 1
    fi
    COG_VENV="$(readlink -f "$COG_PATH")"
    COG_VERSION="$(basename "$COG_VENV" | sed 's/cog\(.*\)-python.*//')"
    echo "COG_VERSION not set, using default $COG_VERSION"
else
    COG_PATH="$MONOBASE_PREFIX/cog/latest/cog$COG_VERSION-python$PYTHON_VERSION"
    if [ ! -d "$COG_PATH" ]; then
        echo "Cog $COG_VERSION not in monobase, installing..."
        uv venv --python "$PYTHON_VERSION" /root/cog
        case "$COG_VERSION" in
            https://*) pkg="cog @ $COG_VERSION" ;;
            *)         pkg="cog==$COG_VERSION"  ;;
        esac
        VIRTUAL_ENV=/root/cog uv pip install "$pkg"
        COG_VENV=/root/cog
    else
        COG_VENV="$(readlink -f "$COG_PATH")"
    fi
fi

########################################

if [ -z "${MONOBASE_GEN_ID:-}" ]; then
    latest="$MONOBASE_PREFIX/monobase/latest"
    if [ -h "$latest" ]; then
        gdir="$(readlink -f "$latest")"
    else
        # TODO: remove once we roll a new version
        gdir="$(find "$MONOBASE_PREFIX/monobase" -mindepth 2 -maxdepth 2 -name .done -type f -exec dirname {} \; | sort | tail -n 1)"
    fi
    MONOBASE_GEN_ID="$(basename "$gdir" | sed 's/^g0\{0,4\}//')"
    echo "MONOBASE_GEN_ID not set, using latest $MONOBASE_GEN_ID"
fi

MONOBASE_PATH="$MONOBASE_PREFIX/monobase/$(printf 'g%05d' "$MONOBASE_GEN_ID")"
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

COG_PYTHONPATH="$COG_VENV/lib/python$PYTHON_VERSION/site-packages"
VENV_PYTHONPATH="$VIRTUAL_ENV/lib/python$PYTHON_VERSION/site-packages"
export PYTHONPATH="$COG_PYTHONPATH:$VENV_PYTHONPATH"

export PATH="$VIRTUAL_ENV/bin:$CUDA_PATH/bin${PATH:+:${PATH}}"
export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:$CUDA_PATH/lib64:$CUDNN_PATH/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
export LIBRARY_PATH="$CUDA_PATH/lib64/stubs"

LD_CACHE_PATH="$MONOBASE_PATH/ld.so.cache.d/cuda$CUDA_VERSION-cudnn$CUDNN_VERSION-python$PYTHON_VERSION"
cp -f "$LD_CACHE_PATH" /etc/ld.so.cache
