monobase
========

Monobase image with all CUDA * CuDNN * Python * Torch dependencies

# Motivation

Monobase aim to solve the following problems with Docker base images:

* 100+ images for all CUDA * CuDNN * Python * Torch combinations
* Many common files across images, e.g. Torch bundled CUDA & CuDNN
* Inefficient space utilization due to Docker layering
* Bumping a package requires rebuilding all base images
* Bumping base image requires rebuilding all model images

# Design

Monobase is a Docker container that runs in two modes:

* As a daemon set on K8S nodes
    * Mounts host path /srv/r8/monobase
    * Installs CUDA, CuDNN, Python, Torch, and other PIP packages
* As a base image for weightless models
    * Mounts host path /srv/r8/monobase as read-only
    * Activate environments based on CUDA, CuDNN, Python, and Torch versions

Monobase is more efficient than base images because:

* Only system packages are baked into the image
* PIP packages are managed by [`uv`](https://github.com/astral-sh/uv) which
  uses hard links for better space utilization
* Bumping a system package requires a new monobase image only
* Bumping a PIP package requires building a new immutable generation
* Building new generation is fast and efficient due to UV cache and hard links
* Immutable generations are easy to reason about
* Daemon set pins the image on K8S nodes and eliminates cache miss

# Operations

A monobase generation is an immutable matrix of CUDA, CuDNN, Python, Torch,
and other PIP packages. To add a generation:

* Add an element to `PROD_MONOGENS` in `src/monogen.py`
* Run `script/update.sh --min-gen-id X` where `X` is the generation ID added
* Verify the new requirements files in `src/requirements/g{X:05d}`
* Check in the new requirements files into Git
* Build and update `monobase` daemon set to the latest image

A few notes about operations:

* Args `--{min,max}-gen-id` set the active generations `[min, max]`
* Readiness probe reports whether the active generations are ready
* Arg `--prune-old-gen` deletes generations older than `--min-gen-id`
* Arg `--clean-uv-cache` cleans UV cache in case of corruption

# Models

When used as a base image for weightless models, the following environment
variables determine the runtime environment:

* `MONOBASE_GEN_ID` - monobase generation to use, latest if unset
* `CUDA_VERSION` - CUDA `major.minor`
* `CUDNN_VERSION` - CuDNN `major`
* `PYTHON_VERSION` - Python `major.minor`
* `TORCH_VERSION` - Torch `major.minor.patch`
