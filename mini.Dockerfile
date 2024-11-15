# vi: filetype=dockerfile

FROM monobase:latest
ENV R8_COG_VERSION=0.11.3
ENV R8_CUDA_VERSION=12.4
ENV R8_CUDNN_VERSION=9
ENV R8_PYTHON_VERSION=3.12
ENV R8_TORCH_VERSION=2.4.1
COPY requirements-user.txt /tmp/requirements.txt
RUN /opt/r8/monobase/build.sh --skip-cuda --mini --requirements /tmp/requirements.txt
