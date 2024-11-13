# vi: filetype=dockerfile

FROM monobase:latest
ENV COG_VERSION=0.11.3
ENV CUDA_VERSION=12.4
ENV CUDNN_VERSION=9
ENV PYTHON_VERSION=3.12
ENV TORCH_VERSION=2.4.1
RUN /opt/r8/monobase/build.sh --mini
