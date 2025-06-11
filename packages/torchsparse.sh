#!/bin/bash

set -euo pipefail

# Torch is needed but not in build requirements
# shellcheck disable=SC1091
source /opt/r8/monobase/activate.sh

# Loosely based on
# https://github.com/pytorch/pytorch/blob/main/.ci/manywheel/build_cuda.sh
# 5.0 is not supported due to missing __hadd2
export TORCH_CUDA_ARCH_LIST='6.0;7.0;7.5;8.0;8.6;9.0'
export FORCE_CUDA=1

git clone https://github.com/mit-han-lab/torchsparse.git

cd torchsparse
project_dir=$PWD

git checkout 385f5ce8718fcae93540511b7f5832f4e71fd835

apt-get update && apt-get install libsparsehash-dev

cd "$project_dir"
python3 setup.py bdist_wheel

find . -name '*.whl' > requirements.txt
# import torchspase fails without GPU device
if [ -e /dev/nvidiactl ]; then
    /build/test.sh requirements.txt 'import torchsparse.backend; "count_cuda" in torchsparse.backend.__dict__'
else
    echo 'GPU not found, add "--gpus all"'
fi

find . -name '*.whl' -exec cp {} /dst \;
