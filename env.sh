#!/bin/bash

# Source this in entry point

if [ -z "$CUDA_VERSION" ]; then
    echo "CUDA_VERSION not set"
    exit 1
fi

if [ -z "$CUDNN_VERSION" ]; then
    echo "CUDNN_VERSION not set"
    exit 1
fi

if [ -z "$PYTHON_VERSION" ]; then
    echo "PYTHON_VERSION not set"
    exit 1
fi

if [ -z "$TORCH_VERSION" ]; then
    echo "TORCH_VERSION not set"
    exit 1
fi

CUDA_PATH="/usr/local/cuda/cuda-$CUDA_VERSION"
CUDA_MAJOR="${CUDA_VERSION//.[0-9]*/}"
CUDNN_PATH="/usr/local/cuda/cudnn-$CUDNN_VERSION-cuda${CUDA_MAJOR}"
VENV_PATH="/usr/local/uv/venv/python$PYTHON_VERSION-torch$TORCH_VERSION"

if ! [ -d "$CUDA_PATH" ]; then
    echo "CUDA $CUDA_VERSION not installed"
    exit 1
fi

if ! [ -d "$CUDNN_PATH" ]; then
    echo "CuDNN $CUDNN_VERSION not installed"
    exit 1
fi

export PATH="$CUDA_PATH/bin${PATH:+:${PATH}}"
export LD_LIBRARY_PATH="$CUDA_PATH/lib64:$CUDNN_PATH/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
export LIBRARY_PATH="$CUDA_PATH/lib64/stubs"

if ! [ -d "$VENV_PATH" ]; then
    echo "Virtual environment $VENV_PATH not installed"
    exit 1
fi

# shellcheck disable=SC1091
source "$VENV_PATH/bin/activate"

LD_CACHE_PATH="/usr/local/etc/ld.so.cache.d/cuda$CUDA_VERSION-cudnn$CUDNN_VERSION-python$PYTHON_VERSION"
ln -f "$LD_CACHE_PATH" /etc/ld.so.cache