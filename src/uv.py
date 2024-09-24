#!/usr/bin/env python3

from collections import namedtuple
import argparse
import json
import os
import os.path
import re
import subprocess
import sys

from config import pip_packages, torch_deps, torch_specs, uv_url
from util import run, Version


def build(args):
    pythons = sorted(list(map(Version.parse, filter(None, args.python.split(',')))))
    torches = sorted(list(map(Version.parse, filter(None, args.torch.split(',')))))

    # Downloading uv
    uv = '/usr/local/bin/uv'
    if not os.path.exists(uv):
        print('Downloading uv...')
        os.makedirs('/usr/local/bin', exist_ok=True)
        cmd = ['bash', '-c', f'curl -fsSL {uv_url} | tar -xz --strip-components=1 -C /usr/local/bin']
        run(cmd, args)

    # Cache must be in the same volume mount for hardlink to work
    os.environ['UV_CACHE_DIR'] = '/usr/local/uv/cache'
    os.environ['UV_PYTHON_INSTALL_DIR'] = '/usr/local/uv/python'
    os.environ['UV_TOOL_BIN_DIR'] = '/usr/local/bin'
    os.environ['UV_TOOL_DIR'] = '/usr/local/uv/tools'

    os.environ['UV_COMPILE_BYTECODE'] = 'true'
    os.environ['UV_LINK_MODE'] = 'hardlink'
    os.environ['UV_PYTHON_PREFERENCE'] = 'only-managed'

    # Install Python
    print(f'Installing python {" ".join(map(str, pythons))}...')
    cmd = [uv, 'python', 'install'] + list(map(str, pythons))
    run(cmd, args)

    cudas = set()
    p = re.compile('^cuda-(?P<version>\d+\.\d+)$')
    for e in os.listdir('/usr/local/cuda'):
        m = p.search(e)
        if not m:
            continue
        cudas.add(m.group('version'))

    # Set up virtual environments
    venvs = []
    for p in pythons:
        for t in torches:
            tv = Version.parse(f'{t.major}.{t.minor}')
            if tv not in torch_specs or p < torch_specs[tv].python_min or p > torch_specs[tv].python_max:
                continue
            for cuda in torch_specs[tv].cudas:
                if cuda not in cudas:
                    continue

                cu = f'cu{cuda.replace(".", "")}'
                venv = f'python{p}-torch{t}-{cu}'
                venvs.append(venv)
                venv_dir = os.path.join('/usr/local/uv/venv', venv)
                if os.path.exists(venv_dir):
                    continue

                print(f'Building venv {venv}...')
                cmd = [uv, 'venv', '--seed',  '--relocatable', '--python', str(p), venv_dir]
                run(cmd, args)

                print(f'Installing torch {t} in {venv}...')
                os.environ['VIRTUAL_ENV'] = venv_dir
                deps = torch_deps[str(t)]
                cmd = [uv, 'pip', 'install',
                       '--extra-index-url', f'https://download.pytorch.org/whl/{cu}',
                       f'torch=={t}+{cu}',
                       f'torchaudio=={deps.torchaudio}+{cu}',
                       f'torchvision=={deps.torchvision}+{cu}',] + pip_packages
                run(cmd, args)

    # Versions
    print('Writing versions.json...')
    versions = {
            'python_versions': list(map(str, pythons)),
            'torch_versions': list(map(str, torches)),
            'venvs': venvs,
            }
    with open('/usr/local/uv/versions.json', 'w') as f:
        json.dump(versions, f, indent=4)


parser = argparse.ArgumentParser(description='Build uv layer for monobase image')
parser.add_argument('--python', metavar='VERSION', required=True,
                    help='Python major.minor versions, comma separated')
parser.add_argument('--torch', metavar='VERSION', required=True,
                    help='Torch versions, comma separated')
parser.add_argument('-v', '--verbose', default=False, action='store_true',
                    help='Verbose output')


if __name__ == '__main__':
    args = parser.parse_args()

    if os.path.exists('/.dockerenv') and "IN_CLOUDBUILD" not in os.environ:
        # Build inside a container for:
        # - Platform = Linux
        # - Absolute paths
        # - Hard links
        build(args)
    else:
        src_dir = os.path.dirname(os.path.realpath(__file__))
        base_dir = os.path.realpath(os.path.join(src_dir, os.path.pardir))
        build_dir = os.path.join(base_dir, 'build')
        os.makedirs(build_dir, exist_ok=True)

        cmd = ['docker', 'run', '--rm',
               '--user', f'{os.getuid()}:{os.getgid()}',
               '--volume', f'{src_dir}:/src',
               '--volume', f'{build_dir}:/usr/local',
               'monobase:build',
               f'/src/{os.path.basename(__file__)}'] + sys.argv[1:]
        run(cmd, args)
