#!/bin/sh

# Source this in entry point

########################################

# Required environment variables

if [ -z "${R8_CUDA_VERSION:-}" ]; then
    echo "R8_CUDA_VERSION not set"
    return 1
fi

if [ -z "${R8_CUDNN_VERSION:-}" ]; then
    echo "R8_CUDNN_VERSION not set"
    return 1
fi

if [ -z "${R8_PYTHON_VERSION:-}" ]; then
    echo "R8_PYTHON_VERSION not set"
    return 1
fi

if [ -z "${R8_TORCH_VERSION:-}" ]; then
    echo "R8_TORCH_VERSION not set"
    return 1
fi

########################################

# Cog

if [ -z "${R8_COG_VERSION:-}" ]; then
    COG_PATH="$MONOBASE_PREFIX/cog/latest/default-python$R8_PYTHON_VERSION"
    if [ ! -d "$COG_PATH" ]; then
        echo "Cog $COG_PATH does not exist"
        return 1
    fi
    COG_VENV="$(readlink -f "$COG_PATH")"
    R8_COG_VERSION="$(basename "$COG_VENV" | sed 's/cog\(.*\)-python.*/\1/')"
    echo "R8_COG_VERSION not set, using default $R8_COG_VERSION"
else
    case $R8_COG_VERSION in
        https://*)
            name=$(printf '%s' "$R8_COG_VERSION" | sha256sum | cut -c 1-8)
            pkg="cog @ $R8_COG_VERSION"
            ;;
        *)
            name=$R8_COG_VERSION
            pkg="cog==$R8_COG_VERSION"
            ;;
    esac

    COG_PATH="$MONOBASE_PREFIX/cog/latest/cog$name-python$R8_PYTHON_VERSION"
    if [ ! -d "$COG_PATH" ]; then
        echo "Cog $R8_COG_VERSION not in monobase, installing..."
        uv venv --python "$R8_PYTHON_VERSION" /root/cog
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
CUDA_PATH="$MONOBASE_PATH/cuda$R8_CUDA_VERSION"
CUDA_MAJOR="$(echo "$R8_CUDA_VERSION" | sed 's/\..\+//')"
CUDA_SUFFIX="$(echo "$R8_CUDA_VERSION" | sed 's/\.//')"
CUDNN_PATH="$MONOBASE_PATH/cudnn$R8_CUDNN_VERSION-cuda${CUDA_MAJOR}"
export VIRTUAL_ENV="$MONOBASE_PATH/python$R8_PYTHON_VERSION-torch$R8_TORCH_VERSION-cu$CUDA_SUFFIX"

if ! [ -d "$CUDA_PATH" ]; then
    echo "CUDA $R8_CUDA_VERSION not installed"
    return 1
fi

if ! [ -d "$CUDNN_PATH" ]; then
    echo "CuDNN $R8_CUDNN_VERSION not installed"
    return 1
fi

if ! [ -d "$VIRTUAL_ENV" ]; then
    echo "Virtual environment $VIRTUAL_ENV not installed"
    return 1
fi

COG_PYTHONPATH="$COG_VENV/lib/python$R8_PYTHON_VERSION/site-packages"
VENV_PYTHONPATH="$VIRTUAL_ENV/lib/python$R8_PYTHON_VERSION/site-packages"
export PYTHONPATH="$COG_PYTHONPATH:$VENV_PYTHONPATH"

export PATH="$VIRTUAL_ENV/bin:$CUDA_PATH/bin${PATH:+:${PATH}}"

# NVIDIA Container Toolkit mounts drivers here
NCT_PATH=/usr/lib/x86_64-linux-gnu
# NCCL is not part of CUDA or CuDNN and required by vLLM
NCCL_PATH="$VENV_PYTHONPATH/nvidia/nccl/lib"
export LD_LIBRARY_PATH="$NCT_PATH:$CUDA_PATH/lib64:$CUDNN_PATH/lib:$NCCL_PATH${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
export LIBRARY_PATH="$CUDA_PATH/lib64/stubs"

LD_CACHE_PATH="$MONOBASE_PATH/ld.so.cache.d/cuda$R8_CUDA_VERSION-cudnn$R8_CUDNN_VERSION-python$R8_PYTHON_VERSION"
cp -f "$LD_CACHE_PATH" /etc/ld.so.cache
