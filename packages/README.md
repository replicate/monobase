packages
========

Build custom packages with Monobase

# Introduction

Many Python packages do not provide pre-compiled binary wheels and require
some custom dependencies and steps to build.

This script allows us to build such packages using the same base environment
as monobase, i.e. a specific Python + Torch + CUDA combination.

# Usage

Start an interactive shell in a container with the specific base environment:

```
./build.py --python 3.10 --torch 2.3.1 --cuda 12.1
```

Build a package with a given script:

```
./build.py --python 3.10 --torch 2.3.1 --cuda 12.1 --dst . fairseq.sh

```

`--dst .` mounts the current working directory as `/dst` where the build
artifacts should be copied to.

# Build Script

A typical build script should look like this


```
set -eou pipefail

# Check out source
git clone <repo>
cd <repo>
git checkout <tag>

# Other customization, e.g. patches

# UV uses clang/clang++ by default
# Add CC=gcc CXX=g++ to override
uv build

# Copy tarball and wheel to output directory
cp -r dist/* /dst
```
