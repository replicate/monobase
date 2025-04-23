#!/bin/bash

set -euo pipefail

# Torch is needed but not in build requirements
# shellcheck disable=SC1091
source /opt/r8/monobase/activate.sh

# Loosely based on
# https://github.com/pytorch/pytorch/blob/main/.ci/manywheel/build_cuda.sh
export TORCH_CUDA_ARCH_LIST='5.0;6.0;7.0;7.5;8.0;8.6;9.0'

git clone https://github.com/autonomousvision/mip-splatting.git

cd mip-splatting
project_dir=$PWD

git checkout dda02ab5ecf45d6edb8c540d9bb65c7e451345a9

# uv build fails due to missing header, potential bug?
cd "$project_dir/submodules/diff-gaussian-rasterization"
python3 setup.py bdist_wheel

cd "$project_dir/submodules/simple-knn"
python3 setup.py bdist_wheel

cd "$project_dir"
find . -name '*.whl' > requirements.txt
/build/test.sh requirements.txt 'import diff_gaussian_rasterization; import simple_knn'

find . -name '*.whl' -exec cp {} /dst \;
