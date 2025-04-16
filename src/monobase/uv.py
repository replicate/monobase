import argparse
import logging
import os.path
import subprocess
from typing import Optional

from opentelemetry import trace

from monobase.torch import get_torch_spec, torch_deps
from monobase.util import Version, mark_done, require_done_or_rm, tracer

log = logging.getLogger(__name__)


def cuda_suffix(cuda_version: str) -> str:
    return 'cpu' if cuda_version == 'cpu' else f'cu{cuda_version.replace(".", "")}'


def torch_index_url(cuda_version: str, nightly: bool) -> str:
    prefix = 'https://download.pytorch.org/whl'
    cu = cuda_suffix(cuda_version)
    if nightly:
        return f'{prefix}/nightly/{cu}'
    else:
        return f'{prefix}/{cu}'


def index_args(
    torch_version: Optional[str], cuda_version: str, user: bool
) -> list[str]:
    # Nightly builds e.g. 2.6.1.dev20241121
    nightly = torch_version is not None and '.dev' in torch_version
    return [
        # --extra-index-url has high priority than --index-url
        '--extra-index-url',
        torch_index_url(cuda_version, nightly),
        # PyPI is the default index URL
        '--index-url',
        'https://pypi.org/simple',
        # For base venv, prefer first index i.e. Torch, as it might pin some transitives
        # e.g. numpy 1.x over 2.x
        # For user venv, unsafe is fine since we filter out those already in base anyway
        '--index-strategy',
        'unsafe-first-match' if user else 'first-index',
    ]


def pip_packages(
    torch_version: Version, python_version: str, cuda_version: str, pip_pkgs: list[str]
) -> list[str]:
    deps = torch_deps[torch_version]
    cu = cuda_suffix(cuda_version)
    if torch_version.extra:
        # Nightly build
        prefix = torch_index_url(cuda_version, True)
        py = f'cp{python_version.replace(".", "")}'
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
    # Numpy was bumped to 2.x in PyTorch index around early 2025
    # Pin it to 1.x for older Torch versions to avoid a breaking change
    if torch_version < Version.parse('2.6.0'):
        pkgs += ['numpy<2.0.0']
    # Older Torch versions do not bundle CUDA or CuDNN
    nvidia_pkgs = []
    if cu != 'cpu' and torch_version < Version.parse('2.2.0'):
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
) -> bool:
    trace.get_current_span().set_attributes(
        {
            'requirements_dir': rdir,
            'python_full_version': python_full_version,
            'torch_version': torch_version if torch_version is not None else '',
            'cuda_version': cuda_version,
            'pip_pkgs': str(pip_pkgs),
        }
    )

    p = Version.parse(python_version)
    t = Version.parse(torch_version)
    spec = get_torch_spec(t)
    if spec is None:
        return False
    if p < spec.python_min or p > spec.python_max:
        return False
    if cuda_version not in spec.cudas:
        return False

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
    # We specify --python-platform here because update is usually ran outside the container
    # e.g. on a developer's Mac
    cmd = ['uv', 'pip', 'compile', '--python-platform', 'x86_64-unknown-linux-gnu']
    cmd = cmd + emit_args + index_args(torch_version, cuda_version, False) + ['-']
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
        print(e.stdout)
        print(e.stderr)
        raise e
    return True


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
    spec = get_torch_spec(t)
    if spec is None:
        return
    if p < spec.python_min or p > spec.python_max:
        return
    if cuda_version not in spec.cudas:
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
    cmd += index_args(torch_version, cuda_version, False)
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
