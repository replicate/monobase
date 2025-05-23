import argparse
import logging
import os.path
import subprocess
from typing import Optional

from monobase.util import (
    Version,
    mark_done,
    parse_requirements,
    require_done_or_rm,
    setup_logging,
)
from monobase.uv import cuda_suffix, index_args

log = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description='Build monobase user layer')
parser.add_argument(
    '--prefix',
    metavar='PATH',
    default='/srv/r8/monobase',
    help='prefix for monobase',
)
parser.add_argument(
    '--requirements',
    metavar='FILE',
    help='Python requirements.txt for user layer',
)
parser.add_argument(
    '--override',
    metavar='FILE',
    help='Python requirements.txt for overriding versions',
)


def freeze(uv: str, vdir: str) -> str:
    cmd = [uv, 'pip', 'freeze']
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = vdir
    proc = subprocess.run(cmd, check=True, env=env, capture_output=True, text=True)
    return proc.stdout


def build_user_venv(args: argparse.Namespace) -> None:
    # User venv must not be inside args.prefix which might be mounted read-only
    udir = '/root/.venv'
    if require_done_or_rm(udir):
        log.info(f'User venv in {udir} is complete')
        return

    log.info(f'Building user venv {udir}...')

    python_version = os.environ['R8_PYTHON_VERSION']
    torch_version = os.environ.get('R8_TORCH_VERSION')
    cuda_version = os.environ.get('R8_CUDA_VERSION', 'cpu')

    uv = os.path.join(args.prefix, 'bin', 'uv')

    cdir = os.path.realpath(os.path.join(args.prefix, 'cog', 'latest'))
    vdir = os.path.realpath(os.path.join(cdir, f'default-python{python_version}'))
    log.info(f'Freezing Cog venv {vdir}...')
    cog_req = freeze(uv, vdir)
    with open('/root/requirements-cog.txt', 'w') as f:
        f.write(cog_req)
    cog_versions = parse_requirements(cog_req)

    if torch_version is None:
        # Missing Torch version, skipping monobase venv
        mono_req = ''
        mono_versions: dict[str, str | Version] = {}
    else:
        gdir = os.path.realpath(os.path.join(args.prefix, 'monobase', 'latest'))
        venv = (
            f'python{python_version}-torch{torch_version}-{cuda_suffix(cuda_version)}'
        )
        vdir = os.path.join(gdir, venv)
        log.info(f'Freezing monobase venv {vdir}...')
        mono_req = freeze(uv, vdir)
        with open('/root/requirements-mono.txt', 'w') as f:
            f.write(mono_req)
        mono_versions = parse_requirements(mono_req)

    log.info(f'Creating user venv {udir}...')
    cmd = ['uv', 'venv', '--python', python_version, udir]
    subprocess.run(cmd, check=True)

    with open(args.requirements, 'r') as f:
        user_req = f.read()
    # Combine monobase and user requirements to detect unsatisfiable requirements
    # Reasons:
    # * mono_req is from uv pip freeze and contains exact versions
    # * It has higher precedence than user_req in PYTHONPATH
    # * Duplicates in user_req are removed
    #
    # Example: mono_req has jinja2==3.1.3 for torch==2.5.1
    # user_req with jinja2==3.1.4, jinja2<3.0.0, or jina2>=4.0.0 will fail
    # while jina2>=3.0.0 should pass
    #
    # Cog req is not included as we manage that and will reduce its dependencies
    combined_req = '\n'.join(mono_req.splitlines() + user_req.splitlines())

    log.info(f'Compiling user requirements {args.requirements}...')
    cmd = [uv, 'pip', 'compile']
    # Override version conflicts, e.g.
    if args.override is not None:
        cmd = cmd + ['--override', args.override]
    # PyPI is inconsistent with Torch index and may include nvidia packages for CPU torch
    # Use the same Torch index instead
    cmd = cmd + index_args(torch_version, cuda_version, True) + ['-']
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = udir
    if 'R8_PYTHONPATH' in env:
        # R8_PYTHON_PATH is from activate.sh and contains Cog + monobase + user venvs
        # Restore it before working on user venv
        env['PYTHONPATH'] = env['R8_PYTHONPATH']
    try:
        proc = subprocess.run(
            cmd, check=True, env=env, input=combined_req, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(e.stderr)
        raise e

    user_req = proc.stdout
    user_versions = parse_requirements(user_req)
    if 'torch' in user_versions and torch_version is None:
        error_statement = f'You did not specify a torch version in your requirements.txt, but your build requires torch=={user_versions["torch"]}, please specify that in your requirements.txt.'
        print(error_statement)
        raise ValueError(error_statement)
    keys = set(
        list(cog_versions.keys())
        + list(mono_versions.keys())
        + list(user_versions.keys())
    )
    for k in sorted(keys):
        cvs = cog_versions.get(k)
        mvs = mono_versions.get(k)
        uvs = user_versions.get(k)
        vs: list[Optional[str | Version]] = [cvs, mvs, uvs]
        majors: set[str | int] = set()
        minors: set[str | int] = set()
        for v in vs:
            if v is None:
                continue
            elif type(v) is str:
                majors.add(v)
                minors.add(v)
            elif type(v) is Version:
                majors.add(v.major)
                minors.add(v.minor)
        # Do not this because we install a custom hf_transfer with metrics
        if k == 'hf-transfer':
            continue
        if len(majors) == 1 and len(minors) > 1:
            log.warning(
                f'possible incompatible versions for {k}: cog=={cvs}, mono=={mvs}, user=={uvs}'
            )
        elif len(majors) > 1 and len(minors) > 1:
            log.error(
                f'probable incompatible versions for {k}: cog=={cvs}, mono=={mvs}, user=={uvs}'
            )

    user_req_path = '/root/requirements-user.txt'
    with open(user_req_path, 'w') as f:
        for k, uvs in sorted(user_versions.items()):
            mvs = mono_versions.get(k)
            if mvs is not None:
                # Only warn exclusions if base and user layers have different versions
                if mvs != uvs:
                    log.warning(
                        f'excluding {k} from user venv: mono=={mvs}, user=={uvs}'
                    )
                continue
            if k == uvs and type(uvs) is str and os.path.exists(uvs):
                # Local path, always include, even if it might conflict with monobase, e.g. ./torch-2.6.0.dev*.whl
                print(k, file=f)
            elif type(uvs) is str:
                print(f'{k} @ {uvs}', file=f)
            else:
                print(f'{k}=={uvs}', file=f)
    cmd = [uv, 'pip', 'install', '--no-deps', '--requirement', user_req_path]
    cmd += index_args(torch_version, cuda_version, True)
    subprocess.run(cmd, check=True, env=env)

    mark_done(
        udir,
        kind='user',
        python_version=python_version,
        torch_version=torch_version,
        cuda_version=cuda_version,
    )
    log.info(f'User venv installed in {udir}')


if __name__ == '__main__':
    setup_logging()
    build_user_venv(parser.parse_args())
