# This file is meant to be sourced in any environment that requires the monobase layers to
# be active.

########################################

# Required environment variables

if [ -z "${R8_PYTHON_VERSION:-}" ]; then
    echo "R8_PYTHON_VERSION not set"
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
    https://*|file://*)
        pkg=cog
        if echo "$R8_COG_VERSION" | grep -q coglet; then
            pkg=coglet
        fi
        cog_name="$pkg$(printf '%s' "$R8_COG_VERSION" | sha256sum | cut -c 1-8)"
        pkg="$pkg @ $R8_COG_VERSION"
        ;;
    coglet==*)
        cog_name="$(echo "$R8_COG_VERSION" | sed 's/coglet==/coglet/')"
        pkg=""
        ;;
    *)
        cog_name="cog$R8_COG_VERSION"
        pkg="cog==$R8_COG_VERSION"
        ;;
    esac

    COG_PATH="$MONOBASE_PREFIX/cog/latest/$cog_name-python$R8_PYTHON_VERSION"
    if [ ! -d "$COG_PATH" ]; then
        if [ -z "$pkg" ]; then
            echo "Cog $R8_COG_VERSION not installed"
            return 1
        fi
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
    gdir="$(readlink -f "$latest")"
    MONOBASE_GEN_ID="$(basename "$gdir" | sed 's/^g0\{0,4\}//')"
    echo "MONOBASE_GEN_ID not set, using latest $MONOBASE_GEN_ID"
fi

MONOBASE_PATH="$MONOBASE_PREFIX/monobase/$(printf 'g%05d' "$MONOBASE_GEN_ID")"
if [ -n "${R8_CUDA_VERSION:-}" ] && [ -n "${R8_CUDNN_VERSION:-}" ]; then
    CUDA_PATH="$MONOBASE_PATH/cuda$R8_CUDA_VERSION"
    CUDA_MAJOR="$(echo "$R8_CUDA_VERSION" | sed 's/\..\+//')"
    CUDA_SUFFIX="$(echo "$R8_CUDA_VERSION" | sed 's/\.//')"
    CUDNN_PATH="$MONOBASE_PATH/cudnn$R8_CUDNN_VERSION-cuda${CUDA_MAJOR}"
    export VIRTUAL_ENV="$MONOBASE_PATH/python$R8_PYTHON_VERSION-torch$R8_TORCH_VERSION-cu$CUDA_SUFFIX"
    export PATH="$VIRTUAL_ENV/bin:$CUDA_PATH/bin${PATH:+:${PATH}}"
else
    export VIRTUAL_ENV="$MONOBASE_PATH/python$R8_PYTHON_VERSION-torch$R8_TORCH_VERSION"
    export PATH="$VIRTUAL_ENV/bin${PATH:+:${PATH}}"
fi

if ! [ -d "$VIRTUAL_ENV" ]; then
    echo "Virtual environment $VIRTUAL_ENV not installed"
    return 1
fi

COG_PYTHONPATH="$COG_VENV/lib/python$R8_PYTHON_VERSION/site-packages"
MONO_PYTHONPATH="$VIRTUAL_ENV/lib/python$R8_PYTHON_VERSION/site-packages"
USER_PYTHONPATH="$MONOBASE_PREFIX/user/lib/python$R8_PYTHON_VERSION/site-packages"

if [ -d "$USER_PYTHONPATH" ]; then
    export PYTHONPATH="$COG_PYTHONPATH:$MONO_PYTHONPATH:$USER_PYTHONPATH"
else
    export PYTHONPATH="$COG_PYTHONPATH:$MONO_PYTHONPATH"
fi

if [ -n "${R8_CUDA_VERSION:-}" ] && [ -n "${R8_CUDNN_VERSION:-}" ]; then
    # NVIDIA Container Toolkit mounts drivers here
    NCT_PATH=/usr/lib/x86_64-linux-gnu
    # NCCL is not part of CUDA or CuDNN and required by vLLM
    NCCL_PATH="$MONO_PYTHONPATH/nvidia/nccl/lib"
    export LD_LIBRARY_PATH="$NCT_PATH:$CUDA_PATH/lib64:$CUDNN_PATH/lib:$NCCL_PATH${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
    export LIBRARY_PATH="$CUDA_PATH/lib64/stubs"
    LD_CACHE_PATH="$MONOBASE_PATH/ld.so.cache.d/cuda$R8_CUDA_VERSION-cudnn$R8_CUDNN_VERSION-python$R8_PYTHON_VERSION"
    export R8_ATTRIBUTES_FILES="${COG_VENV}/.done ${CUDA_PATH}/.done ${CUDNN_PATH}/.done ${VIRTUAL_ENV}/.done"
else
    LD_CACHE_PATH="$MONOBASE_PATH/ld.so.cache.d/python$R8_PYTHON_VERSION"
    export R8_ATTRIBUTES_FILES="${COG_VENV}/.done ${VIRTUAL_ENV}/.done"
fi

cp -f "$LD_CACHE_PATH" /etc/ld.so.cache
