import argparse
import logging
import os.path
import subprocess

from opentelemetry import trace

from monobase.torch import torch_deps, torch_specs
from monobase.util import Version, mark_done, require_done_or_rm, tracer

log = logging.getLogger(__name__)


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
    torch_version: Version, python_version: str, cuda_version: str, pip_pkgs: list[str]
) -> list[str]:
    deps = torch_deps[torch_version]
    cu = cuda_suffix(cuda_version)
    if torch_version.extra:
        prefix = torch_index_url(torch_version, cuda_version)
        py = f'cp{python_version.replace('.', '')}'
        pkgs = [
            f'torch @ {prefix}/torch-{torch_version}%2B{cu}-{py}-{py}-linux_x86_64.whl',
            f'torchaudio @ {prefix}/torchaudio-{deps.torchaudio}%2B{cu}-{py}-{py}-linux_x86_64.whl',
            f'torchvision @ {prefix}/torchvision-{deps.torchvision}%2B{cu}-{py}-{py}-linux_x86_64.whl',
        ]
    else:
        pkgs = [
            f'torch=={torch_version}+{cu}',
            f'torchaudio=={deps.torchaudio}+{cu}',
            f'torchvision=={deps.torchvision}+{cu}',
        ]
    # Older Torch versions do not bundle CUDA or CuDNN
    nvidia_pkgs = []
    if torch_version < Version.parse('2.2.0'):
        nvidia_pkgs = [
            'nvidia-cublas',
            'nvidia-cuda-cupti',
            'nvidia-cuda-nvrtc',
            'nvidia-cuda-runtime',
            'nvidia-cudnn',
            'nvidia-cufft',
            'nvidia-curand',
            'nvidia-cusolver',
            'nvidia-cusparse',
            'nvidia-nccl',
            'nvidia-nvtx',
        ]
        if cu.startswith('cu12'):
            nvidia_pkgs.append('nvidia-nvjitlink')
        nvidia_pkgs = [f'{p}-{cu[:4]}' for p in nvidia_pkgs]
    return pkgs + pip_pkgs + nvidia_pkgs


@tracer.start_as_current_span('update_venv')
def update_venv(
    rdir: str,
    tmp: str,
    python_version: str,
    python_full_version: str,
    torch_version: str,
    cuda_version: str,
    pip_pkgs: list[str],
) -> None:
    trace.get_current_span().set_attributes(
        {
            'requirements_dir': rdir,
            'python_full_version': python_full_version,
            'torch_version': torch_version,
            'cuda_version': cuda_version,
            'pip_pkgs': str(pip_pkgs),
        }
    )

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
    vdir = os.path.join(tmp, venv)

    log.info(f'Creating venv {venv}...')
    cmd = ['uv', 'venv', '--python', python_full_version, vdir]
    subprocess.run(cmd, check=True)

    log.info(f'Running pip compile in {venv}...')
    # Emit extra info for debugging
    emit_args = [
        '--emit-index-url',
        '--emit-find-links',
        '--emit-build-options',
        '--emit-index-annotation',
    ]
    cmd = ['uv', 'pip', 'compile', '--python-platform', 'x86_64-unknown-linux-gnu']
    cmd = cmd + emit_args + index_args(t, cuda_version) + ['-']
    pkgs = pip_packages(t, python_version, cuda_version, pip_pkgs)
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
        log.error(e.stdout)
        log.error(e.stderr)
        raise e


@tracer.start_as_current_span('install_venv')
def install_venv(
    args: argparse.Namespace,
    rdir: str,
    gdir: str,
    python_version: str,
    python_full_version: str,
    torch_version: str,
    cuda_version: str,
) -> None:
    trace.get_current_span().set_attributes(
        {
            'requirements_dir': rdir,
            'python_full_version': python_full_version,
            'torch_version': torch_version,
            'cuda_version': cuda_version,
        }
    )

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
    if require_done_or_rm(vdir):
        log.info(f'Venv {venv} in {vdir} is complete')
        return

    log.info(f'Creating venv {venv}...')
    uv = os.path.join(args.prefix, 'bin', 'uv')
    cmd = [uv, 'venv', '--python', python_full_version, vdir]
    subprocess.run(cmd, check=True)

    log.info(f'Installing Torch {t} in {venv}...')

    requirements = os.path.join(rdir, f'{venv}.txt')
    cmd = [uv, 'pip', 'install', '--no-deps', '--requirement', requirements]
    cmd += index_args(t, cuda_version)
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = vdir
    subprocess.run(cmd, check=True, env=env)

    mark_done(
        vdir,
        kind='venv',
        python_version=python_version,
        python_full_version=python_full_version,
        torch_version=torch_version,
        cuda_version=cuda_version,
    )
    log.info(f'Python {python_version} Torch {torch_version} installed in {vdir}')
