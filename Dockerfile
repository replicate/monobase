FROM ubuntu:jammy

ENV UV_CACHE_DIR=/usr/local/uv/cache
ENV UV_PYTHON_INSTALL_DIR=/usr/local/uv/python
ENV UV_TOOL_BIN_DIR=/usr/local/bin
ENV UV_TOOL_DIR=/usr/local/uv/tools

ENV UV_COMPILE_BYTECODE=true
ENV UV_LINK_MODE=hardlink
ENV UV_PYTHON_PREFERENCE=only-managed

COPY build env.sh /usr/local/
