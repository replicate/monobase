#!/bin/bash

set -euo pipefail

CUDA=( 11.7 11.8 12.1 12.4 )
CUDNN=( 9 )
PYTHON=( 3.8 3.9 3.10 3.11 3.12 )
TORCH=( 2.0.0 2.0.1 2.1.0 2.1.1 2.1.2 2.2.0 2.2.1 2.2.2 2.3.0 2.3.1 2.4.0 2.4.1 )

csv() {
    local IFS=","
    echo "$*"
}

cuda="$(csv "${CUDA[@]}")"
cudnn="$(csv "${CUDNN[@]}")"
python="$(csv "${PYTHON[@]}")"
torch="$(csv "${TORCH[@]}")"

base_dir="$(git rev-parse --show-toplevel)"

"$base_dir/src/cuda.py" -v --cuda="$cuda" --cudnn="$cudnn"
"$base_dir/src/uv.py" -v --python="$python" --torch="$torch"

docker build --tag monobase:latest "$base_dir"
