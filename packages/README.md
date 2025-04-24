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

Build a package with a given script, write wheel files to `.`:

```
./build.py --python 3.10 --torch 2.3.1 --cuda 12.1 --dst . fairseq.sh

```

Current working directory is mounted read-only as `/src` inside the container.

Host `/tmp` is mounted as `/dst` inside the container where build artifacts
should be copied to. Use `--dst .` to mount `$PWD` instead.

# Build Script

A typical build script should look like this


```
set -eou pipefail

# Check out source
git clone <repo>
cd <repo>
git checkout <tag>

# Other customization, e.g. patches

# Build with UV
# UV uses clang/clang++ by default
# Add CC=gcc CXX=g++ to override
uv build

# Or vanilla setuptools if UV fails
python3 setup.py bdist_wheel

# Add wheel files to a requirements.txt
find . -name '*.whl' > requirements.txt

# Test install & import the packages
/build/test.sh requirements.txt 'import <pkg>'

# Copy wheel files to output directory
find . -name '*.whl' -exec cp {} /dst \;
```

# Verify the build

After building the wheel files we can verify them with the same image again.

```
# Start the container
./build.py --python 3.10 --torch 2.3.1 --cuda 12.1

# Activate the environment
source /opt/r8/monobase/activate.sh

# Host $PWD is mounted as /src
# Add wheel files to a requirements.txt
find /src -name '*.whl' > requirements.txt

# Install wheel files and start a Python shell
./build/test.sh requirements.txt

# Test library functionality
import <pkg>
...
```
