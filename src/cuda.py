from collections import namedtuple
from urls import cuda_urls, cudnn_urls

import argparse
import os
import urllib.parse
import re
import shutil
import subprocess

from util import Version, is_done, logger, mark_done


Cuda = namedtuple('Cuda', ['url', 'filename', 'cuda_version', 'driver_version'])
CuDNN = namedtuple('CuDNN', ['url', 'filename', 'cudnn_version', 'cuda_major'])


def build_cudas() -> dict[str, Cuda]:
    p = re.compile(r'^cuda_(?P<cuda>[^_]+)_(?P<driver>[^_]+)_linux.run$')
    cudas = {}
    for u in cuda_urls:
        url = urllib.parse.urlparse(u)
        f = os.path.basename(url.path)
        m = p.search(f)
        cuda = Version.parse(m.group('cuda'))
        driver = Version.parse(m.group('driver'))
        cudas[f'{cuda}_{driver}'] = Cuda(u, f, cuda, driver)
    return cudas


def build_cudnns() -> dict[str, CuDNN]:
    p = re.compile(
            r'^cudnn-linux-x86_64-(?P<cudnn>[^_]+)_cuda(?P<cuda_major>[^-]+)-archive.tar.xz$')
    cudnns = {}
    for u in cudnn_urls:
        url = urllib.parse.urlparse(u)
        f = os.path.basename(url.path)
        m = p.search(f)
        cudnn = Version.parse(m.group('cudnn'))
        cuda_major = int(m.group('cuda_major'))
        cudnns[f'{cudnn}-cuda{cuda_major}'] = CuDNN(u, f, cudnn, cuda_major)
    return cudnns


cudas: dict[str, Cuda] = build_cudas()
cudnns: dict[str, CuDNN] = build_cudnns()


def install_cuda(args: argparse.Namespace, version: str) -> str:
    cdir = f'{args.prefix}/cuda/cuda-{version}'
    if is_done(cdir):
        return cdir

    logger.info(f'Downloading CUDA {version}...')
    cuda = cudas[version]
    file = os.path.join(args.cache, cuda.filename)
    cmd = ['pget', '--force', cuda.url, file]
    subprocess.run(cmd, check=True)

    logger.info(f'Installing CUDA {version}...')
    cmd = [
        '/bin/sh', file, f'--installpath={cdir}',
        '--toolkit', '--override', '--silent',
        '--no-opengl-libs', '--no-man-page', '--no-drm'
    ]
    subprocess.run(cmd, check=True)
    os.remove(file)

    # Remove unused files
    logger.info(f'Deleting unused files for CUDA {version}...')
    shutil.rmtree(os.path.join(cdir, 'compute-sanitizer'), ignore_errors=True)
    shutil.rmtree(os.path.join(cdir, 'extras'), ignore_errors=True)
    shutil.rmtree(os.path.join(cdir, 'gds'), ignore_errors=True)
    shutil.rmtree(os.path.join(cdir, 'libnvvp'), ignore_errors=True)
    shutil.rmtree(os.path.join(cdir, 'nsightee_plugins'), ignore_errors=True)
    shutil.rmtree(os.path.join(cdir, 'nvml'), ignore_errors=True)
    shutil.rmtree(os.path.join(cdir, 'pkgconfig'), ignore_errors=True)
    shutil.rmtree(os.path.join(cdir, 'tools'), ignore_errors=True)

    cmd = ['/bin/sh', '-c', f'rm -rf {cdir}/gds-* {cdir}/nsight-*']
    subprocess.run(cmd, check=True)

    cmd = ['find', cdir, '-name', 'lib*.a', '-delete']
    subprocess.run(cmd, check=True)

    mark_done(cdir)
    logger.info(f'CUDA {version} installed in {cdir}')
    return cdir


def install_cudnn(args: argparse.Namespace, version: str, cuda_major: str) -> str:
    key = f'{version}-cuda{cuda_major}'
    cdir = f'{args.prefix}/cuda/cudnn-{key}'
    if is_done(cdir):
        return cdir

    logger.info(f'Downloading CuDNN {key}...')
    cudnn = cudnns[key]
    file = os.path.join(args.cache, cudnn.filename)
    cmd = ['pget', '--force', cudnn.url, file]
    subprocess.run(cmd, check=True)

    logger.info(f'Installing CuDNN {key}...')
    os.makedirs(cdir)
    cmd = ['tar', '-xf', file, '--strip-components=1', '--exclude=lib*.a', '-C', cdir]
    subprocess.run(cmd, check=True)
    os.remove(file)

    mark_done(cdir)
    logger.info(f'CuDNN {key} installed in {cdir}')
    return cdir
