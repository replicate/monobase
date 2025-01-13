# vi: filetype=dockerfile

FROM monobase:latest

ENV R8_COG_VERSION=0.11.3
ENV R8_CUDA_VERSION=12.4
ENV R8_CUDNN_VERSION=9
ENV R8_PYTHON_VERSION=3.12
ENV R8_TORCH_VERSION=2.4.1

########################################
# Layers overlapping with many-mono

COPY requirements-user.txt /tmp/requirements.txt
# Install a single mini-mono venv
RUN /opt/r8/monobase/build.sh --skip-cuda --mini

########################################
# Start of user layers
# These should be ready to push as is

# Install a user venv
# Do not reinstall uv & pget
RUN /opt/r8/monobase/run.sh monobase.build --skip-cuda --mini --requirements /tmp/requirements.txt
