# vi: filetype=dockerfile

# - If hostname is monobase-builder-*
#   - Runs as a DaemonSet on each worker
#   - Builds PREFIX for model images
# - Else
#   - Runs as base image for models
#   - Mounts PREFIX as host path

FROM ubuntu:jammy

ARG PREFIX=/srv/r8/monobase

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

ENV MONOBASE_PREFIX=$PREFIX
ENV PATH=$MONOBASE_PREFIX/bin:$PATH
ENV PYTHONPATH=/opt/r8
ENV UV_CACHE_DIR=$PREFIX/uv/cache
ENV UV_PYTHON_INSTALL_DIR=$PREFIX/uv/python
ENV UV_TOOL_BIN_DIR=$PREFIX/bin
ENV UV_TOOL_DIR=$PREFIX/uv/tools

ENV UV_COMPILE_BYTECODE=true
ENV UV_LINK_MODE=hardlink
ENV UV_PYTHON_PREFERENCE=only-managed

# ca-certificates - HTTPS
# curl - download uv, PGET, etc.
# libxml2 - CUDA installer
# rdfind - find duplicate CUDA .so files
# xz-utils - CuDNN tarball

RUN apt-get update \
    && apt-get install -y \
        ca-certificates \
        curl \
        libxml2 \
        rdfind \
        xz-utils \
        build-essential \
        ca-certificates \
        cmake \
        curl \
        ffmpeg \
        findutils \
        g++ \
        gcc \
        git \
        libavcodec-dev \
        libbz2-dev \
        libcairo2-dev \
        libffi-dev \
        libfontconfig1 \
        libgirepository1.0-dev \
        libgl1 \
        libgl1-mesa-glx \
        libglib2.0-0 \
        liblzma-dev \
        libncurses5-dev \
        libncursesw5-dev \
        libopencv-dev \
        libreadline-dev \
        libsm6 \
        libsndfile1 \
        libsqlite3-dev \
        libssl-dev \
        libunistring-dev \
        libxext6 \
        libxrender1 \
        llvm \
        make \
        sox \
        tini \
        tk-dev \
        unzip \
        wget \
        xz-utils \
        zip \
        zlib1g-dev \
        zstd \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/tini /sbin/tini
COPY src/monobase /opt/r8/monobase
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/opt/r8/monobase/build.sh", "--help"]
