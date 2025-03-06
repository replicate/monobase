# This file is meant to be sourced in any environment that requires the monobase layers to
# be active.

ERROR=0
WARNING=1
INFO=2
DEBUG=3

VERBOSE=${VERBOSE:-2}  # Default verbosity is INFO (2)

log_error() {
    if [ "$VERBOSE" -ge "$ERROR" ]; then
        echo "[ERROR] $1"
    fi
}

log_warning() {
    if [ "$VERBOSE" -ge "$WARNING" ]; then
        echo "[WARNING] $1"
    fi
}

log_info() {
    if [ "$VERBOSE" -ge "$INFO" ]; then
        echo "[INFO] $1"
    fi
}

log_debug() {
    if [ "$VERBOSE" -ge "$DEBUG" ]; then
        echo "[DEBUG] $1"
    fi
}

########################################

# Required environment variables

if [ -z "${R8_PYTHON_VERSION:-}" ]; then
    log_error "R8_PYTHON_VERSION not set"
    return 1
fi

########################################

# Cog

if [ -z "${R8_COG_VERSION:-}" ]; then
    COG_PATH="$MONOBASE_PREFIX/cog/latest/default-python$R8_PYTHON_VERSION"
    if [ ! -d "$COG_PATH" ]; then
        log_error "Cog $COG_PATH does not exist"
        return 1
    fi
    COG_VENV="$(readlink -f "$COG_PATH")"
    R8_COG_VERSION="$(basename "$COG_VENV" | sed 's/\(cog\(let\)\?\)\(.*\)-python.*/\1==\3/')"
    log_warning "R8_COG_VERSION not set, using default $R8_COG_VERSION"
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
    coglet*)
        if [ "$R8_COG_VERSION" = coglet ]; then
            cog_name=cogletlatest
        else
            cog_name="$(echo "$R8_COG_VERSION" | sed 's/coglet==/coglet/')"
        fi
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
            log_error "Cog $R8_COG_VERSION not installed"
            return 1
        fi
        log_warning "Cog $R8_COG_VERSION not in monobase, installing..."
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
    log_info "MONOBASE_GEN_ID not set, using latest $MONOBASE_GEN_ID"
fi

MONOBASE_PATH="$MONOBASE_PREFIX/monobase/$(printf 'g%05d' "$MONOBASE_GEN_ID")"

if [ -n "${R8_CUDA_VERSION:-}" ] && [ -n "${R8_CUDNN_VERSION:-}" ]; then
    CUDA_PATH="$MONOBASE_PATH/cuda$R8_CUDA_VERSION"
    export LIBRARY_PATH="$CUDA_PATH/lib64/stubs"
    PATH="$CUDA_PATH/bin${PATH:+:${PATH}}"

    CUDA_MAJOR="$(echo "$R8_CUDA_VERSION" | sed 's/\..\+//')"
    CUDNN_PATH="$MONOBASE_PATH/cudnn$R8_CUDNN_VERSION-cuda${CUDA_MAJOR}"

    # NVIDIA Container Toolkit mounts drivers here
    NCT_PATH=/usr/lib/x86_64-linux-gnu
    LD_LIBRARY_PATH="$NCT_PATH:$CUDA_PATH/lib64:$CUDNN_PATH/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"

    LD_CACHE_PATH="$MONOBASE_PATH/ld.so.cache.d/cuda$R8_CUDA_VERSION-cudnn$R8_CUDNN_VERSION-python$R8_PYTHON_VERSION"
    cp -f "$LD_CACHE_PATH" /etc/ld.so.cache

    TORCH_CUDA_SUFFIX="cu$(echo "$R8_CUDA_VERSION" | sed 's/\.//')"
else
    TORCH_CUDA_SUFFIX="cpu"
fi


# Cog venv is guaranteed to be present
# Use Python interpretor from there
PATH="$COG_VENV/bin${PATH:+:${PATH}}"

# Layer Cog venv first
COG_PYTHONPATH="$COG_VENV/lib/python$R8_PYTHON_VERSION/site-packages"
PYTHONPATH="$COG_PYTHONPATH"

# Append Monobase venv if Torch version is set
if [ -n "${R8_TORCH_VERSION:-}" ]; then
    MONO_VENV="$MONOBASE_PATH/python$R8_PYTHON_VERSION-torch$R8_TORCH_VERSION-$TORCH_CUDA_SUFFIX"
    MONO_PYTHONPATH="$MONO_VENV/lib/python$R8_PYTHON_VERSION/site-packages"
    PYTHONPATH="$PYTHONPATH:$MONO_PYTHONPATH"

    # NCCL is not part of CUDA or CuDNN and required by vLLM
    NCCL_PATH="$MONO_PYTHONPATH/nvidia/nccl/lib"
    LD_LIBRARY_PATH="$NCCL_PATH${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
fi

# Append user venv last
USER_PYTHONPATH="/root/.venv/lib/python$R8_PYTHON_VERSION/site-packages"
if [ -d "$USER_PYTHONPATH" ]; then
    PYTHONPATH="$PYTHONPATH:$USER_PYTHONPATH"
fi

export PATH
export PYTHONPATH
export LD_LIBRARY_PATH
