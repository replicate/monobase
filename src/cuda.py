#!/usr/bin/env python3

from collections import namedtuple
import argparse
import json
import os.path
import re
import shutil
import string
import subprocess
import sys
import urllib.parse

from matrix import cuda_urls, cudnn_urls
from util import run, Version


Cuda = namedtuple('Cuda', ['url', 'filename', 'cuda_version', 'driver_version'])
CuDNN = namedtuple('CuDNN', ['url', 'filename', 'cudnn_version', 'cuda_major'])


# Select latest CUDA version for each CUDA major.minor
def select_cudas(versions):
    p = re.compile(r'^cuda_(?P<cuda>[^_]+)_(?P<driver>[^_]+)_linux.run$')
    matrix = {}
    for u in cuda_urls:
        url = urllib.parse.urlparse(u)
        f = os.path.basename(url.path)
        m = p.search(f)
        cuda = Version.parse(m.group('cuda'))
        driver = Version.parse(m.group('driver'))
        k = f'{cuda.major}.{cuda.minor}'
        if len(versions) > 0 and k not in versions:
            continue
        if k not in matrix:
            matrix[k] = []
        matrix[k].append(Cuda(u, f, cuda, driver))
    cudas = {}
    for k, v in matrix.items():
        cudas[k] = sorted(v, key=lambda x: x.cuda_version, reverse=True)[0]
    return cudas


# Select latest versions for each CuDNN major + CUDA major
def select_cudnns(versions, cuda_majors):
    p = re.compile(r'^cudnn-linux-x86_64-(?P<cudnn>[^_]+)_cuda(?P<cuda>[^-]+)-archive.tar.xz$')
    matrix = {}
    for u in cudnn_urls:
        url = urllib.parse.urlparse(u)
        f = os.path.basename(url.path)
        m = p.search(f)
        cudnn = Version.parse(m.group('cudnn'))
        cuda = int(m.group('cuda'))
        if len(versions) > 0 and str(cudnn.major) not in versions:
            continue
        if cuda not in cuda_majors:
            continue
        k = f'{cudnn.major}-cuda{cuda}'
        if k not in matrix:
            matrix[k] = []
        matrix[k].append(CuDNN(u, f, cudnn, cuda))
    cudnns = {}
    for k, v in matrix.items():
        cudnns[k] = sorted(v, key=lambda x: x.cudnn_version, reverse=True)[0]
    return cudnns


def build(args):
    args = parser.parse_args()

    build_dir = '/usr/local/cuda'
    cache_dir = '/mnt/cache'

    cudas = set(filter(None, args.cuda.split(',')))
    cudas = select_cudas(cudas)
    cuda_majors = set(c.cuda_version.major for c in cudas.values())

    cudnns = set(filter(None, args.cudnn.split(',')))
    cudnns = select_cudnns(cudnns, cuda_majors)

    # Download CUDA
    for k, cuda in sorted(cudas.items()):
        out = os.path.join(cache_dir, cuda.filename)
        if os.path.exists(out):
            continue
        print(f'Downloading CUDA {k}...')
        cmd = ['curl', '-fsSL', cuda.url, '-o', out]
        run(cmd, args)

    # Download CuDNN
    for k, cudnn in sorted(cudnns.items()):
        out = os.path.join(cache_dir, cudnn.filename)
        if os.path.exists(out):
            continue
        print(f'Downloading CuDNN {k}...')
        cmd = ['curl', '-fsSL', cudnn.url, '-o', out]
        run(cmd, args)

    # Install CUDA
    for k, cuda in sorted(cudas.items()):
        out = os.path.join(build_dir, f'cuda-{k}')
        if os.path.exists(out):
            continue
        print(f'Installing CUDA {k}...')
        runfile = os.path.join(cache_dir, cuda.filename)
        cmd = ['/bin/sh', runfile, '--silent', f'--installpath={out}',
               '--toolkit', '--no-opengl-libs', '--no-man-page', '--no-drm']
        run(cmd, args)

        # Remove unused files
        shutil.rmtree(os.path.join(out, 'compute-sanitizer'), ignore_errors=True)
        shutil.rmtree(os.path.join(out, 'extras'), ignore_errors=True)
        shutil.rmtree(os.path.join(out, 'gds'), ignore_errors=True)
        shutil.rmtree(os.path.join(out, 'libnvvp'), ignore_errors=True)
        shutil.rmtree(os.path.join(out, 'nsightee_plugins'), ignore_errors=True)
        shutil.rmtree(os.path.join(out, 'nvml'), ignore_errors=True)
        shutil.rmtree(os.path.join(out, 'pkgconfig'), ignore_errors=True)
        run(['/bin/sh', '-c', f'rm -rf {out}/gds-* {out}/nsight-*'], args)
        run(['find', out, '-name', 'lib*.a', '-delete'], args)

    # Install CuDNN
    for k, cudnn in sorted(cudnns.items()):
        out = os.path.join(build_dir, f'cudnn-{k}')
        if os.path.exists(out):
            continue
        print(f'Installing CuDNN {k}...')
        os.makedirs(out)
        tarball = os.path.join(cache_dir, cudnn.filename)
        cmd = ['tar', '-xf', tarball, '--strip-components=1', '--exclude=lib*.a', '-C', out]
        run(cmd, args)

    # Versions
    print('Writing versions.json...')
    versions = {
            'cuda_versions': [str(c.cuda_version) for c in sorted(cudas.values())],
            'cudnn_versions': [f'{c.cudnn_version}-cuda{c.cuda_major}' for c in sorted(cudnns.values())],
            }
    with open(os.path.join(build_dir, 'versions.json'), 'w') as f:
        json.dump(versions, f, indent=4)


parser = argparse.ArgumentParser(description='Build CUDA layer for monobase image')
parser.add_argument('--cache-dir', metavar='PATH', default='cache',
                    help='CUDA cache directory')
parser.add_argument('--cuda', metavar='VERSIONS', default='',
                    help='CUDA major.minor versions, comma separated')
parser.add_argument('--cudnn', metavar='VERSIONS', default='',
                    help='CuDNN major versions, comma separated')
parser.add_argument('-v', '--verbose', default=False, action='store_true',
                    help='Verbose output')


if __name__ == '__main__':
    args = parser.parse_args()

    if os.path.exists('/.dockerenv'):
        # Build inside a container for:
        # - Absolute paths
        # - Sandboxing
        build(args)
    else:
        src_dir = os.path.dirname(os.path.realpath(__file__))
        base_dir = os.path.realpath(os.path.join(src_dir, os.path.pardir))
        build_dir = os.path.join(base_dir, 'build/cuda')
        cache_dir = os.path.abspath(args.cache_dir)
        os.makedirs(build_dir, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)

        cmd = ['docker', 'run', '-it', '--rm',
               '--user', f'{os.getuid()}:{os.getgid()}',
               '--volume', f'{src_dir}:/src',
               '--volume', f'{build_dir}:/usr/local/cuda',
               '--volume', f'{cache_dir}:/mnt/cache',
               'python:latest',
               f'/src/{os.path.basename(__file__)}'] + sys.argv[1:]
        run(cmd, args)
