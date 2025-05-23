#!/bin/bash

set -euo pipefail

git clone https://github.com/facebookresearch/fairseq.git

cd fairseq
# https://github.com/facebookresearch/fairseq/pull/4667
git checkout d81fac8163364561fd6cd9d82b6ee1ba502c3526

uv build

find . -name '*.whl' > requirements.txt
/build/test.sh requirements.txt 'import fairseq'

find . -name '*.whl' -exec cp {} /dst \;
