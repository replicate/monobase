import argparse
import logging
import os
import re
import shutil
import subprocess
import urllib.parse
from dataclasses import dataclass
from multiprocessing import Pool

from monobase.urls import cuda_urls, cudnn_urls
from monobase.util import (
    Version,
    mark_done,
    require_done_or_rm,
    setup_logging,
)

R8_PACKAGE_PREFIX = 'https://monobase-packages.replicate.delivery'

log = logging.getLogger(__name__)


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


def tar_and_delete(path: str, file: str) -> None:
    # https://www.gnu.org/software//tar/manual/html_section/Reproducibility.html
    tar_flags = [
        '--sort=name',
        '--format=posix',
        '--pax-option=exthdr.name=%d/PaxHeaders/%f',
        '--pax-option=delete=atime,delete=ctime,delete=btime,delete=mtime',
        '--mtime=0',
        '--numeric-owner',
        '--owner=0',
        '--group=0',
        '--mode=go+u,go-w',
    ]
    tar_env = {
        'LC_ALL': 'C',
        'TZ': 'UTC',
    }
    cmd = (
        ['tar', '-C', path]
        + tar_flags
        + ['--zstd', '-cf', file]
        + sorted(os.listdir(path))
    )
    subprocess.run(cmd, check=True, env=tar_env)
    shutil.rmtree(path, ignore_errors=True)


def pget(args: argparse.Namespace, url: str, file: str) -> None:
    cmd = [
        f'{args.prefix}/bin/pget',
        '--pid-file',
        '/tmp/pget.pid',
        url,
        file,
    ]
    subprocess.run(cmd, check=True)


def build_cuda_tarball(args: argparse.Namespace, version: str) -> None:
    tf = os.path.join(args.cache, 'cuda', f'monobase-cuda-{version}.tar.zst')
    if os.path.exists(tf):
        return

    cuda = CUDAS[version]
    file = os.path.join(args.cache, 'cuda', cuda.filename)
    if not os.path.exists(file):
        log.info(f'Downloading CUDA {version}...')
        pget(args, cuda.url, file)

    log.info(f'Installing CUDA {version}...')
    cdir = os.path.join(args.prefix, 'cuda', f'cuda-{version}')
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
    log.info(f'Deleting unused files for CUDA {version}...')
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

    log.info(f'Creating CUDA tarball {tf}...')
    tar_and_delete(cdir, tf)


def build_cudnn_tarball(
    args: argparse.Namespace, version: str, cuda_major: str
) -> None:
    key = f'{version}-cuda{cuda_major}'
    tf = os.path.join(args.cache, 'cudnn', f'monobase-cudnn-{key}.tar.zst')
    if os.path.exists(tf):
        return

    cudnn = CUDNNS[key]
    file = os.path.join(args.cache, 'cudnn', cudnn.filename)
    if not os.path.exists(file):
        log.info(f'Downloading CuDNN {key}...')
        pget(args, cudnn.url, file)

    log.info(f'Installing CuDNN {key}...')
    cdir = os.path.join(args.prefix, 'cuda', f'cudnn-{key}')
    os.makedirs(cdir, exist_ok=True)
    cmd = ['tar', '-xf', file, '--strip-components=1', '--exclude=lib*.a', '-C', cdir]
    subprocess.run(cmd, check=True)

    log.info(f'Creating CuDNN tarball {tf}...')
    tar_and_delete(cdir, tf)


def install_cuda(args: argparse.Namespace, version: str) -> str:
    cdir = os.path.join(args.prefix, 'cuda', f'cuda-{version}')
    if require_done_or_rm(cdir):
        log.info(f'CUDA {version} in {cdir} is complete')
        return cdir

    if os.environ.get('CI_SKIP_CUDA') is not None:
        os.makedirs(cdir, exist_ok=True)
        mark_done(cdir, kind='cuda', version=version, skipped=True)
        log.info(f'CUDA {version} skipped in {cdir}')
        return cdir

    filename = f'monobase-cuda-{version}.tar.zst'
    path = os.path.join(args.cache, 'cuda', filename)
    url = f'file://{path}'
    if not os.path.exists(path):
        log.info(f'Downloading CUDA {version}...')
        url = f'{R8_PACKAGE_PREFIX}/cuda/{filename}'
        pget(args, url, path)

    log.info(f'Installing CUDA {version}...')
    os.makedirs(cdir, exist_ok=True)
    cmd = ['tar', '-xf', path, '-C', cdir]
    subprocess.run(cmd, check=True)

    mark_done(cdir, kind='cuda', version=version, url=url)
    log.info(f'CUDA {version} installed in {cdir}')
    return cdir


def install_cudnn(args: argparse.Namespace, version: str, cuda_major: str) -> str:
    key = f'{version}-cuda{cuda_major}'
    cdir = os.path.join(args.prefix, 'cuda', f'cudnn-{key}')
    if require_done_or_rm(cdir):
        log.info(f'CuDNN {key} in {cdir} is complete')
        return cdir

    if os.environ.get('CI_SKIP_CUDA') is not None:
        os.makedirs(cdir, exist_ok=True)
        mark_done(cdir, kind='cudnn', version=version, skipped=True)
        log.info(f'CuDNN {key} skipped in {cdir}')
        return cdir

    filename = f'monobase-cudnn-{key}.tar.zst'
    path = os.path.join(args.cache, 'cudnn', filename)
    url = f'file://{path}'
    if not os.path.exists(path):
        log.info(f'Downloading CuDNN {key}...')
        url = f'{R8_PACKAGE_PREFIX}/cudnn/{filename}'
        pget(args, url, path)

    log.info(f'Installing CuDNN {key}...')
    os.makedirs(cdir, exist_ok=True)
    cmd = ['tar', '-xf', path, '-C', cdir]
    subprocess.run(cmd, check=True)

    mark_done(cdir, kind='cudnn', version=version, url=url)
    log.info(f'CuDNN {key} installed in {cdir}')
    return cdir


parser = argparse.ArgumentParser(description='Build monobase environment')
parser.add_argument(
    '--prefix',
    metavar='PATH',
    default='/srv/r8/monobase',
    help='prefix for monobase',
)
parser.add_argument(
    '--cache',
    metavar='PATH',
    default='/var/cache/monobase',
    help='cache for monobase',
)


def build_tarballs(args: argparse.Namespace) -> None:
    with Pool() as pool:
        results = []
        os.makedirs(os.path.join(args.cache, 'cuda'), exist_ok=True)
        for k in CUDAS.keys():
            r = pool.apply_async(build_cuda_tarball, (args, k))
            results.append(r)
        os.makedirs(os.path.join(args.cache, 'cudnn'), exist_ok=True)
        for v in CUDNNS.values():
            a = (args, str(v.cudnn_version), str(v.cuda_major))
            r = pool.apply_async(build_cudnn_tarball, a)
            results.append(r)
        for r in results:
            r.wait()


if __name__ == '__main__':
    setup_logging()
    build_tarballs(parser.parse_args())
