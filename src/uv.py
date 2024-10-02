import argparse
import os.path
import subprocess

from torch import torch_deps, torch_specs
from util import Version, is_done, logger, mark_done


def cuda_suffix(cuda_version: str) -> str:
    return f'cu{cuda_version.replace('.', '')}'


def pip_index_url(torch_version: Version, cuda_version: str):
    prefix = 'https://download.pytorch.org/whl'
    if torch_version.extra:
        prefix = f'{prefix}/nightly'
    return f'{prefix}/{cuda_suffix(cuda_version)}'


def pip_packages(torch_version: Version,
                 cuda_version: str,
                 pip_pkgs: list[str]) -> tuple[str, list[str]]:
    deps = torch_deps[torch_version]
    cu = cuda_suffix(cuda_version)
    pkgs = [
        f'torch=={torch_version}+{cu}',
        f'torchaudio=={deps.torchaudio}+{cu}',
        f'torchvision=={deps.torchvision}+{cu}',
    ] + pip_pkgs
    return pkgs


def update_venv(
        rdir: str,
        tmp: str,
        python_version: str,
        python_full_version: str,
        torch_version: str,
        cuda_version: str,
        pip_pkgs: list[str]):
    p = Version.parse(python_version)
    t = Version.parse(torch_version)
    tv = Version.parse(f'{t.major}.{t.minor}')
    if tv not in torch_specs:
        return
    if p < torch_specs[tv].python_min or p > torch_specs[tv].python_max:
        return
    if cuda_version not in torch_specs[tv].cudas:
        return

    venv = f'python{python_version}-torch{torch_version}-{cuda_suffix(cuda_version)}'
    vdir = f'{tmp}/{venv}'

    logger.info(f'Creating venv {venv}...')
    cmd = ['uv', 'venv', '--python', python_full_version, vdir]
    subprocess.run(cmd, check=True)

    logger.info(f'Running pip compile in {venv}...')
    url = pip_index_url(t, cuda_version)
    cmd = [
        'uv', 'pip', 'compile',
        '--python-platform', 'x86_64-unknown-linux-gnu',
        '--extra-index-url', url,
        '--emit-index-url',
        '--emit-find-links',
        '--emit-build-options',
        '--emit-index-annotation',
        '-',
    ]
    pkgs = pip_packages(t, cuda_version, pip_pkgs)
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = vdir
    proc = subprocess.run(cmd, check=True, env=env, input='\n'.join(pkgs), capture_output=True, text=True)

    requirements = os.path.join(rdir, f'{venv}.txt')
    with open(requirements, 'w') as f:
        f.write(proc.stdout)


def install_venv(args: argparse.Namespace,
                 rdir: str,
                 gdir: str,
                 python_version: str,
                 python_full_version: str,
                 torch_version: str,
                 cuda_version: str) -> None:
    p = Version.parse(python_version)
    t = Version.parse(torch_version)
    tv = Version.parse(f'{t.major}.{t.minor}')
    if tv not in torch_specs:
        return
    if p < torch_specs[tv].python_min or p > torch_specs[tv].python_max:
        return
    if cuda_version not in torch_specs[tv].cudas:
        return

    venv = f'python{python_version}-torch{torch_version}-{cuda_suffix(cuda_version)}'
    vdir = os.path.join(gdir, venv)
    if is_done(vdir):
        return

    logger.info(f'Creating venv {venv}...')
    uv = os.path.join(args.prefix, 'bin', 'uv')
    cmd = [uv, 'venv', '--python', python_full_version, vdir]
    subprocess.run(cmd, check=True)

    logger.info(f'Installing Torch {t} in {venv}...')

    url = pip_index_url(t, cuda_version)
    requirements = os.path.join(rdir, f'{venv}.txt')
    cmd = [
        uv, 'pip', 'install',
        '--no-deps',
        '--extra-index-url', url,
        '--requirement', requirements,
    ]
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = vdir
    subprocess.run(cmd, check=True, env=env)

    mark_done(vdir)
    logger.info(f'Python {python_version} Torch {torch_version} installed in {vdir}')
