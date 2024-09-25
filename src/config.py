#!/usr/bin/env python3

from collections import namedtuple
from util import Version

####################
# CUDA + CuDNN
####################

# https://developer.nvidia.com/cuda-downloads
cuda_prefix = 'https://developer.download.nvidia.com/compute/cuda'

cuda_urls = [
        f'{cuda_prefix}/12.6.1/local_installers/cuda_12.6.1_560.35.03_linux.run',
        f'{cuda_prefix}/12.6.0/local_installers/cuda_12.6.0_560.28.03_linux.run',
        f'{cuda_prefix}/12.5.1/local_installers/cuda_12.5.1_555.42.06_linux.run',
        f'{cuda_prefix}/12.5.0/local_installers/cuda_12.5.0_555.42.02_linux.run',
        f'{cuda_prefix}/12.4.1/local_installers/cuda_12.4.1_550.54.15_linux.run',
        f'{cuda_prefix}/12.4.0/local_installers/cuda_12.4.0_550.54.14_linux.run',
        f'{cuda_prefix}/12.3.2/local_installers/cuda_12.3.2_545.23.08_linux.run',
        f'{cuda_prefix}/12.3.1/local_installers/cuda_12.3.1_545.23.08_linux.run',
        f'{cuda_prefix}/12.3.0/local_installers/cuda_12.3.0_545.23.06_linux.run',
        f'{cuda_prefix}/12.2.2/local_installers/cuda_12.2.2_535.104.05_linux.run',
        f'{cuda_prefix}/12.2.1/local_installers/cuda_12.2.1_535.86.10_linux.run',
        f'{cuda_prefix}/12.2.0/local_installers/cuda_12.2.0_535.54.03_linux.run',
        f'{cuda_prefix}/12.1.1/local_installers/cuda_12.1.1_530.30.02_linux.run',
        f'{cuda_prefix}/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run',
        f'{cuda_prefix}/12.0.1/local_installers/cuda_12.0.1_525.85.12_linux.run',
        f'{cuda_prefix}/12.0.0/local_installers/cuda_12.0.0_525.60.13_linux.run',
        f'{cuda_prefix}/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run',
        f'{cuda_prefix}/11.7.1/local_installers/cuda_11.7.1_515.65.01_linux.run',
        f'{cuda_prefix}/11.7.0/local_installers/cuda_11.7.0_515.43.04_linux.run',
        f'{cuda_prefix}/11.6.2/local_installers/cuda_11.6.2_510.47.03_linux.run',
        f'{cuda_prefix}/11.6.1/local_installers/cuda_11.6.1_510.47.03_linux.run',
        f'{cuda_prefix}/11.6.0/local_installers/cuda_11.6.0_510.39.01_linux.run',
        ]

# https://developer.nvidia.com/cudnn-downloads
cudnn_prefix = 'https://developer.download.nvidia.com/compute/cudnn/redist/cudnn/linux-x86_64'

cudnn_urls = [
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


# Torch releases bundle specific versions of CUDA and CuDNN
# https://github.com/pytorch/pytorch/blob/main/.ci/docker/common/install_cuda.sh
torch_cuda_deps = {
        '12.4': '12.4.1_550.54.15',
        '12.1': '12.1.1_530.30.02',
        '11.8': '11.8.0_520.61.05',
        }

# https://github.com/pytorch/pytorch/commits/main/.ci/docker/common/install_cudnn.sh
torch_cudnn_deps = {
        '9': '9.1.0.70',
        '8': '8.9.7.29',
        }


####################
# uv
####################

uv_url = 'https://github.com/astral-sh/uv/releases/download/0.4.10/uv-x86_64-unknown-linux-gnu.tar.gz'

pip_packages = [
        'https://github.com/replicate/cog/archive/refs/heads/add-waiting-env.zip',
        'opencv-python==4.10.0.84',
        ]

TorchSpec = namedtuple('TorchSpec', ['python_min', 'python_max', 'cudas'])

# https://github.com/pytorch/pytorch/blob/main/RELEASE.md#release-compatibility-matrix
torch_specs_dict = {
        '2.5': ('3.9', '3.12', ['11.8', '12.1', '12.4']),
        '2.4': ('3.8', '3.12', ['11.8', '12.1', '12.4']),
        '2.3': ('3.8', '3.11', ['11.8', '12.1']),
        '2.2': ('3.8', '3.11', ['11.8', '12.1']),
        '2.1': ('3.8', '3.11', ['11.8', '12.1']),
        '2.0': ('3.8', '3.11', ['11.7', '11.8']),
        }

torch_specs = dict((Version.parse(k), TorchSpec(Version.parse(pmin), Version.parse(pmax), cudas))
                   for k, (pmin, pmax, cudas) in torch_specs_dict.items())

TorchDeps = namedtuple('TorchDeps', ['torchaudio', 'torchvision'])

torch_deps = {
        '2.4.1': TorchDeps('2.4.1', '0.19.1'),
        '2.4.0': TorchDeps('2.4.0', '0.19.0'),
        '2.3.1': TorchDeps('2.3.1', '0.18.1'),
        '2.3.0': TorchDeps('2.3.0', '0.18.0'),
        '2.2.2': TorchDeps('2.2.2', '0.17.2'),
        '2.2.1': TorchDeps('2.2.1', '0.17.1'),
        '2.2.0': TorchDeps('2.2.0', '0.17.0'),
        '2.1.2': TorchDeps('2.1.2', '0.16.2'),
        '2.1.1': TorchDeps('2.1.1', '0.16.1'),
        '2.1.0': TorchDeps('2.1.0', '0.16.0'),
        '2.0.1': TorchDeps('2.0.2', '0.15.2'),
        '2.0.0': TorchDeps('2.0.0', '0.15.0'),
        }


####################
# other
####################

pget_url = 'https://github.com/replicate/pget/releases/latest/download/pget_Linux_x86_64'
