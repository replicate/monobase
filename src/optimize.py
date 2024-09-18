#!/usr/bin/env python3

import argparse
import os
import re
import sys
from util import run


def build(args):
    args = parser.parse_args()

    cudas = {}
    cudnns = {}
    cuda_p = re.compile(r'^cuda-(?P<version>\d+\.\d+)$')
    cudnn_p = re.compile(r'^cudnn-(?P<major>\d+)-cuda\d+$')
    for e in os.listdir('/usr/local/cuda'):
        if e.startswith('cuda-'):
            cudas[cuda_p.search(e).group('version')] = e
        if e.startswith('cudnn-'):
            cudnns[cudnn_p.search(e).group('major')] = e

    pythons = {}
    p = re.compile(r'^cpython-(?P<version>\d+\.\d+)\.\d+-linux-x86_64-gnu$')
    for e in os.listdir('/usr/local/uv/python'):
        m = p.search(e)
        if not m:
            continue
        pythons[m.group('version')] = e

    # Update ld.so.cache for each CUDA + CuDNN + Python combination
    for cuda_version, cuda in cudas.items():
        for cudnn_major, cudnn in cudnns.items():
            for python_major, python in pythons.items():
                k = f'cuda{cuda_version}-cudnn{cudnn_major}-python{python_major}'
                print(f'Updating ld.so.cache for {k}...')
                dirs = [
                        f'/usr/local/cuda/{cuda}/lib64',
                        f'/usr/local/cuda/{cudnn}/lib',
                        f'/usr/local/uv/python/{python}/lib',
                        ]
                cache_dir = '/usr/local/etc/ld.so.cache.d'
                os.makedirs(cache_dir, exist_ok=True)
                run(['ldconfig', '-C', f'{cache_dir}/{k}'] + dirs, args)

    venvs = os.listdir('/usr/local/uv/venv')
    p = re.compile(r'^python(?P<python>\d+\.\d+)-torch\d+\.\d+\.\d+-cu\d+$')
    for venv in venvs:
        pv = p.search(venv).group('python')
        # FIXME: implement this


parser = argparse.ArgumentParser(description='Optimize build for monobase image')
parser.add_argument('-v', '--verbose', default=False, action='store_true',
                    help='Verbose output')


if __name__ == '__main__':
    args = parser.parse_args()

    if os.path.exists('/.dockerenv'):
        build(args)
    else:
        src_dir = os.path.dirname(os.path.realpath(__file__))
        base_dir = os.path.realpath(os.path.join(src_dir, os.path.pardir))
        build_dir = os.path.join(base_dir, 'build')

        cmd = ['docker', 'run', '-it', '--rm',
               '--user', f'{os.getuid()}:{os.getgid()}',
               '--volume', f'{src_dir}:/src',
               '--volume', f'{build_dir}:/usr/local',
               'python:latest',
               f'/src/{os.path.basename(__file__)}'] + sys.argv[1:]
        run(cmd, args)
