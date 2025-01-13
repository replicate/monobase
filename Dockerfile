# vi: filetype=dockerfile
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS build

RUN apt-get update \
    && apt-get install -y git \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src
ADD . .
ENV UV_LINK_MODE=copy
RUN if $(git rev-parse --is-shallow-repository); then git fetch --unshallow; fi  \
    && GIT_DESC="$(git describe --always --dirty --tags)" \
    && if [ "$(echo "${GIT_DESC}" | cut -c1-10)" = 'refs/pull/' ]; then \
         export SETUPTOOLS_SCM_PRETEND_VERSION='v0.0.0.dev+pr'; \
       fi \
    && echo "GIT_DESC=${GIT_DESC}" \
    && echo "SETUPTOOLS_SCM_PRETEND_VERSION=${SETUPTOOLS_SCM_PRETEND_VERSION}" \
    && uv build --sdist --wheel

FROM ubuntu:jammy

ARG PREFIX=/srv/r8/monobase

ENV DEBIAN_FRONTEND=noninteractive
ENV MONOBASE_PREFIX=$PREFIX
ENV PATH=$MONOBASE_PREFIX/bin:$PATH
ENV PYTHONPATH=/opt/r8
ENV TZ=Etc/UTC
ENV UV_CACHE_DIR=$PREFIX/uv/cache
ENV UV_COMPILE_BYTECODE=true
ENV UV_LINK_MODE=hardlink
ENV UV_PYTHON_INSTALL_DIR=$PREFIX/uv/python
ENV UV_PYTHON_PREFERENCE=only-managed
ENV UV_TOOL_BIN_DIR=$PREFIX/bin
ENV UV_TOOL_DIR=$PREFIX/uv/tools

RUN --mount=type=bind,src=.,dst=/src,ro \
    apt-get update \
    && apt-get install -y $(grep -v '^#' </src/apt-dependencies.txt) \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=bind,from=build,target=/tmp/build-layer,ro \
    ln -sv /usr/bin/tini /sbin/tini \
    && mkdir -p /opt/r8/monobase /tmp/r8 \
    && tar --strip-components=1 -C /tmp/r8 -xf $(find /tmp/build-layer/src/dist -name '*.tar.gz' | head -1) \
    && cp -v /tmp/r8/src/monobase/*.sh /tmp/r8/src/monobase/pget /opt/r8/monobase/ \
    && rsync -av /tmp/r8/src/monobase/requirements /opt/r8/monobase/ \
    && find /tmp/build-layer/src/dist/ -type f \
    && cp -v $(find /tmp/build-layer/src/dist/ -name '*.whl' | head -1) /opt/r8/ \
    && rm -rf /tmp/r8

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/opt/r8/monobase/run.sh", "monobase.build", "--help"]
