#!/bin/bash

set -euo pipefail

git clone https://github.com/autonomousvision/mip-splatting.git

cd mip-splatting
project_dir=$PWD

git checkout dda02ab5ecf45d6edb8c540d9bb65c7e451345a9

export TORCH_CUDA_ARCH_LIST='7.0;7.5;8.0;8.6+PTX'

cd "$project_dir/submodules/diff-gaussian-rasterization"
# uv build fails due to missing header, potential bug?
python3 setup.py bdist_wheel
cp dist/* /dst

cd "$project_dir/submodules/simple-knn"
python3 setup.py bdist_wheel
cp dist/* /dst
