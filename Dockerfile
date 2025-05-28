# vi: filetype=dockerfile
FROM ubuntu:jammy

ARG PREFIX=/srv/r8/monobase

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
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

RUN --mount=type=bind,src=.,dst=/src,ro \
    ln -sv /usr/bin/tini /sbin/tini \
    && mkdir -p /opt/r8/monobase \
    && cp -r /src/src/monobase/*.sh /src/src/monobase/*.py /src/src/monobase/requirements /opt/r8/monobase/

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/opt/r8/monobase/run.sh", "monobase.build", "--help"]
