import argparse
import logging
import os.path
import subprocess

from torch import torch_deps, torch_specs
from util import Version, is_done, mark_done


def cuda_suffix(cuda_version: str) -> str:
    return f'cu{cuda_version.replace('.', '')}'


def torch_index_url(torch_version: Version, cuda_version: str) -> str:
    prefix = 'https://download.pytorch.org/whl'
    if torch_version.extra:
        prefix = f'{prefix}/nightly'
    return f'{prefix}/{cuda_suffix(cuda_version)}'


def index_args(torch_version: Version, cuda_version: str) -> list[str]:
    return [
        # --extra-index-url has high priority than --index-url
        '--extra-index-url',
        torch_index_url(torch_version, cuda_version),
        # PyPI is the default index URL
        '--index-url',
        'https://pypi.org/simple',
        # Prefer first index i.e. Torch, as it might pin some transitives
        # e.g. numpy 1.x over 2.x
        '--index-strategy',
        'first-index',
    ]


def pip_packages(
    torch_version: Version, cuda_version: str, pip_pkgs: list[str]
) -> list[str]:
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
    pip_pkgs: list[str],
) -> None:
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

    logging.info(f'Creating venv {venv}...')
    cmd = ['uv', 'venv', '--python', python_full_version, vdir]
    subprocess.run(cmd, check=True)

    logging.info(f'Running pip compile in {venv}...')
    # Emit extra info for debugging
    emit_args = [
        '--emit-index-url',
        '--emit-find-links',
        '--emit-build-options',
        '--emit-index-annotation',
    ]
    cmd = ['uv', 'pip', 'compile', '--python-platform', 'x86_64-unknown-linux-gnu']
    cmd = cmd + emit_args + index_args(t, cuda_version) + ['-']
    pkgs = pip_packages(t, cuda_version, pip_pkgs)
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = vdir
    try:
        proc = subprocess.run(
            cmd,
            check=True,
            env=env,
            input='\n'.join(pkgs),
            capture_output=True,
            text=True,
        )

        requirements = os.path.join(rdir, f'{venv}.txt')
        with open(requirements, 'w') as f:
            f.write(proc.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(e.stdout)
        logging.error(e.stderr)
        raise e


def install_venv(
    args: argparse.Namespace,
    rdir: str,
    gdir: str,
    python_version: str,
    python_full_version: str,
    torch_version: str,
    cuda_version: str,
) -> None:
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

    logging.info(f'Creating venv {venv}...')
    uv = os.path.join(args.prefix, 'bin', 'uv')
    cmd = [uv, 'venv', '--python', python_full_version, vdir]
    subprocess.run(cmd, check=True)

    logging.info(f'Installing Torch {t} in {venv}...')

    requirements = os.path.join(rdir, f'{venv}.txt')
    cmd = [uv, 'pip', 'install', '--no-deps', '--requirement', requirements]
    cmd += index_args(t, cuda_version)
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = vdir
    subprocess.run(cmd, check=True, env=env)

    mark_done(vdir)
    logging.info(f'Python {python_version} Torch {torch_version} installed in {vdir}')
