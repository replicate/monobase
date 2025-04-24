#!/bin/bash

set -euo pipefail

# Torch is needed but not in build requirements
# shellcheck disable=SC1091
source /opt/r8/monobase/activate.sh

# Loosely based on
# https://github.com/pytorch/pytorch/blob/main/.ci/manywheel/build_cuda.sh
export TORCH_CUDA_ARCH_LIST='5.0;6.0;7.0;7.5;8.0;8.6;9.0'

git clone https://github.com/Tencent/Hunyuan3D-2.git

cd Hunyuan3D-2
project_dir=$PWD

git checkout acda9583e719c820b35e084fb3afe3cb9f124519

cd "$project_dir/hy3dgen/texgen/custom_rasterizer"
python3 setup.py bdist_wheel

cd "$project_dir/hy3dgen/texgen/differentiable_renderer"
# Build dependency not declared by the package
uv pip install pybind11
python3 setup.py bdist_wheel

cd "$project_dir"
find . -name '*.whl' > requirements.txt

# Extra dependencies not declared by these packages
# scipy pulls in numpy 2.x but the one from monobase has higher precedence
echo -e 'opencv-python\npygltflib\nscipy' >> requirements.txt


# custom_rasterizer requires torch to be imported first
/build/test.sh requirements.txt 'import torch; import custom_rasterizer; import mesh_processor'

find . -name '*.whl' -exec cp {} /dst \;
