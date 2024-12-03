import argparse
import logging
import os
import re
import shutil
import subprocess
import urllib.parse
from dataclasses import dataclass

from monobase.urls import cuda_urls, cudnn_urls
from monobase.util import Version, mark_done, require_done_or_rm


@dataclass(frozen=True, order=True)
class Cuda:
    url: str
    filename: str
    cuda_version: Version
    driver_version: Version


@dataclass(frozen=True, order=True)
class CuDNN:
    url: str
    filename: str
    cudnn_version: Version
    cuda_major: int


def build_cudas() -> dict[str, Cuda]:
    p = re.compile(r'^cuda_(?P<cuda>[^_]+)_(?P<driver>[^_]+)_linux.run$')
    cudas = {}
    for u in cuda_urls:
        url = urllib.parse.urlparse(u)
        f = os.path.basename(url.path)
        m = p.search(f)
        if m is None:
            raise ValueError(f'Invalid CUDA file name {f}')
        cuda = Version.parse(m.group('cuda'))
        driver = Version.parse(m.group('driver'))
        cudas[f'{cuda}_{driver}'] = Cuda(u, f, cuda, driver)
    return cudas


def build_cudnns() -> dict[str, CuDNN]:
    p = re.compile(
        r'^cudnn-linux-x86_64-(?P<cudnn>[^_]+)_cuda(?P<cuda_major>[^-]+)-archive.tar.xz$'
    )
    cudnns = {}
    for u in cudnn_urls:
        url = urllib.parse.urlparse(u)
        f = os.path.basename(url.path)
        m = p.search(f)
        if m is None:
            raise ValueError(f'Invalid CuDNN file name {f}')
        cudnn = Version.parse(m.group('cudnn'))
        cuda_major = int(m.group('cuda_major'))
        cudnns[f'{cudnn}-cuda{cuda_major}'] = CuDNN(u, f, cudnn, cuda_major)
    return cudnns


CUDAS: dict[str, Cuda] = build_cudas()
CUDNNS: dict[str, CuDNN] = build_cudnns()


def install_cuda(args: argparse.Namespace, version: str) -> str:
    cdir = os.path.join(args.prefix, 'cuda', f'cuda-{version}')
    if require_done_or_rm(cdir):
        return cdir
    if args.skip_cuda:
        os.makedirs(cdir, exist_ok=True)
        mark_done(cdir, kind='cuda', version=version, skipped=True)
        logging.info(f'CUDA {version} skipped in {cdir}')
        return cdir

    cuda = CUDAS[version]
    file = os.path.join(args.cache, cuda.filename)
    if not os.path.exists(file):
        logging.info(f'Downloading CUDA {version}...')
        cmd = [f'{args.prefix}/bin/pget', '--pid-file', '/tmp/pget.pid', cuda.url, file]
        subprocess.run(cmd, check=True)

    logging.info(f'Installing CUDA {version}...')
    cmd = [
        '/bin/sh',
        file,
        f'--installpath={cdir}',
        '--toolkit',
        '--override',
        '--silent',
        '--no-opengl-libs',
        '--no-man-page',
        '--no-drm',
    ]
    subprocess.run(cmd, check=True)

    # Remove unused files
    logging.info(f'Deleting unused files for CUDA {version}...')
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

    mark_done(cdir, kind='cuda', version=version, url=cuda.url)
    logging.info(f'CUDA {version} installed in {cdir}')
    return cdir


def install_cudnn(args: argparse.Namespace, version: str, cuda_major: str) -> str:
    key = f'{version}-cuda{cuda_major}'
    cdir = os.path.join(args.prefix, 'cuda', f'cudnn-{key}')
    if require_done_or_rm(cdir):
        return cdir
    if args.skip_cuda:
        os.makedirs(cdir, exist_ok=True)
        mark_done(cdir, kind='cudnn', version=version, skipped=True)
        logging.info(f'CuDNN {key} skipped in {cdir}')
        return cdir

    cudnn = CUDNNS[key]
    file = os.path.join(args.cache, cudnn.filename)
    if not os.path.exists(file):
        logging.info(f'Downloading CuDNN {key}...')
        cmd = [
            f'{args.prefix}/bin/pget',
            '--pid-file',
            '/tmp/pget.pid',
            cudnn.url,
            file,
        ]
        subprocess.run(cmd, check=True)

    logging.info(f'Installing CuDNN {key}...')
    os.makedirs(cdir, exist_ok=True)
    cmd = ['tar', '-xf', file, '--strip-components=1', '--exclude=lib*.a', '-C', cdir]
    subprocess.run(cmd, check=True)

    mark_done(cdir, kind='cudnn', version=version, url=cudnn.url)
    logging.info(f'CuDNN {key} installed in {cdir}')
    return cdir
