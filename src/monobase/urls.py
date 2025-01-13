import os


def getenv_or(key: str, default: str) -> str:
    value = os.environ.get(key)
    if value is None:
        return default
    value = value.strip()
    if value == '':
        return default
    return value


# https://developer.nvidia.com/cuda-downloads
cuda_prefix = getenv_or(
    'R8_CUDA_PREFIX',
    'https://developer.download.nvidia.com/compute/cuda',
)

cuda_urls = [
    f'{cuda_prefix}/cuda_12.6.3_560.35.05_linux.run',
    f'{cuda_prefix}/cuda_12.6.2_560.35.03_linux.run',
    f'{cuda_prefix}/cuda_12.6.1_560.35.03_linux.run',
    f'{cuda_prefix}/cuda_12.6.0_560.28.03_linux.run',
    f'{cuda_prefix}/cuda_12.5.1_555.42.06_linux.run',
    f'{cuda_prefix}/cuda_12.5.0_555.42.02_linux.run',
    f'{cuda_prefix}/cuda_12.4.1_550.54.15_linux.run',
    f'{cuda_prefix}/cuda_12.4.0_550.54.14_linux.run',
    f'{cuda_prefix}/cuda_12.3.2_545.23.08_linux.run',
    f'{cuda_prefix}/cuda_12.3.1_545.23.08_linux.run',
    f'{cuda_prefix}/cuda_12.3.0_545.23.06_linux.run',
    f'{cuda_prefix}/cuda_12.2.2_535.104.05_linux.run',
    f'{cuda_prefix}/cuda_12.2.1_535.86.10_linux.run',
    f'{cuda_prefix}/cuda_12.2.0_535.54.03_linux.run',
    f'{cuda_prefix}/cuda_12.1.1_530.30.02_linux.run',
    f'{cuda_prefix}/cuda_12.1.0_530.30.02_linux.run',
    f'{cuda_prefix}/cuda_12.0.1_525.85.12_linux.run',
    f'{cuda_prefix}/cuda_12.0.0_525.60.13_linux.run',
    f'{cuda_prefix}/cuda_11.8.0_520.61.05_linux.run',
    f'{cuda_prefix}/cuda_11.7.1_515.65.01_linux.run',
    f'{cuda_prefix}/cuda_11.7.0_515.43.04_linux.run',
    f'{cuda_prefix}/cuda_11.6.2_510.47.03_linux.run',
    f'{cuda_prefix}/cuda_11.6.1_510.47.03_linux.run',
    f'{cuda_prefix}/cuda_11.6.0_510.39.01_linux.run',
]

# https://developer.nvidia.com/cudnn-downloads
cudnn_prefix = getenv_or(
    'R8_CUDNN_PREFIX',
    'https://developer.download.nvidia.com/compute/cudnn/redist/cudnn/linux-x86_64',
)

cudnn_urls = [
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.6.0.74_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.6.0.74_cuda11-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.5.1.17_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.5.1.17_cuda11-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.5.0.50_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.5.0.50_cuda11-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.4.0.58_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.4.0.58_cuda11-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.3.0.75_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.3.0.75_cuda11-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.2.1.18_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.2.1.18_cuda11-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.2.0.82_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.2.0.82_cuda11-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.1.1.17_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.1.1.17_cuda11-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.1.0.70_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.1.0.70_cuda11-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.0.0.312_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-9.0.0.312_cuda11-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-8.9.7.29_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-8.9.7.29_cuda11-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-8.9.6.50_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-8.9.6.50_cuda11-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-8.9.5.30_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-8.9.5.30_cuda11-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-8.9.4.25_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-8.9.4.25_cuda11-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-8.9.3.28_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-8.9.3.28_cuda11-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-8.9.2.26_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-8.9.2.26_cuda11-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-8.9.1.23_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-8.9.1.23_cuda11-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-8.9.0.131_cuda12-archive.tar.xz',
    f'{cudnn_prefix}/cudnn-linux-x86_64-8.9.0.131_cuda11-archive.tar.xz',
]
