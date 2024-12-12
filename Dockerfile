# vi: filetype=dockerfile
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS build

RUN apt-get update \
    && apt-get install -y git \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src
ADD . .
ENV UV_LINK_MODE=copy
RUN if $(git rev-parse --is-shallow-repository); then git fetch --unshallow; fi  \
    && git describe --always --dirty --tags \
    && uv build --sdist

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

ADD ./apt-dependencies.txt /tmp/apt-dependencies.txt
RUN apt-get update \
    && apt-get install -y $(grep -v '^#' </tmp/apt-dependencies.txt) \
    && rm -rf /var/lib/apt/lists/* /tmp/apt-dependencies.txt

RUN --mount=type=bind,from=build,target=/tmp/build-layer,ro \
    ln -sv /usr/bin/tini /sbin/tini \
    && mkdir -p /opt/r8 /tmp/r8 \
    && tar --strip-components=1 -C /tmp/r8 -xf $(find /tmp/build-layer/src/dist -name '*.tar.gz' | head -1) \
    && rsync -av /tmp/r8/src/monobase /opt/r8/ \
    && rm -rf /tmp/r8

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/opt/r8/monobase/build.sh", "--help"]
