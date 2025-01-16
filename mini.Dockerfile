# vi: filetype=dockerfile

FROM monobase:latest

ENV R8_COG_VERSION=0.11.3
ENV R8_CUDA_VERSION=12.4
ENV R8_CUDNN_VERSION=9
ENV R8_PYTHON_VERSION=3.12
ENV R8_TORCH_VERSION=2.4.1

########################################
# Layers overlapping with many-mono

# UV cache is a cache mount and doesn't support hard links
ENV UV_LINK_MODE=copy

# Install a single mini-mono venv
RUN --mount=type=cache,target=/srv/r8/monobase/uv/cache,id=uv-cache \
    --mount=type=cache,target=/var/cache/monobase/,id=var-cache \
    CI_SKIP_CUDA=1 /opt/r8/monobase/run.sh monobase.build --mini

########################################
# Start of user layers
# These should be ready to push as is

# Install APT tarball produced by apt.sh in a separate docker run
RUN --mount=type=bind,src=.,dst=/src,ro \
    tar -xf /src/apt.tar.zst -C /

# Install a user venv
# Disabling UV_COMPILE_BYTECODE because it creates .pyc for the managed Python
# interpretor files while we only want the user venv
RUN --mount=type=cache,target=/srv/r8/monobase/uv/cache,id=uv-cache \
    --mount=type=bind,src=.,dst=/src,ro \
    CI_SKIP_CUDA=1 UV_COMPILE_BYTECODE=0 /opt/r8/monobase/run.sh monobase.user --requirements /src/requirements-user.txt

ENV VERBOSE=0
WORKDIR "/src"
ENTRYPOINT ["/usr/bin/tini", "--", "/opt/r8/monobase/exec.sh"]
CMD ["python3", "-m", "cog.server.http"]
