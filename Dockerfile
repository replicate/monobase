FROM ubuntu:jammy

ENV UV_CACHE_DIR=/usr/local/uv/cache
ENV UV_PYTHON_INSTALL_DIR=/usr/local/uv/python
ENV UV_TOOL_BIN_DIR=/usr/local/bin
ENV UV_TOOL_DIR=/usr/local/uv/tools

ENV UV_COMPILE_BYTECODE=true
ENV UV_LINK_MODE=hardlink
ENV UV_PYTHON_PREFERENCE=only-managed

RUN apt-get update && apt-get install -y --no-install-recommends \
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
        tk-dev \
        unzip \
        wget \
        xz-utils \
        zip \
        zlib1g-dev \
        zstd \
        && rm -rf /var/lib/apt/lists/*

COPY build env.sh /usr/local/
