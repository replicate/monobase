import argparse
import logging
import os.path
import subprocess
from typing import Optional

from util import Version, is_done, mark_done, parse_requirements
from uv import cuda_suffix


def freeze(uv: str, vdir: str) -> str:
    cmd = [uv, 'pip', 'freeze']
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = vdir
    proc = subprocess.run(cmd, check=True, env=env, capture_output=True, text=True)
    return proc.stdout


def build_user_venv(args: argparse.Namespace) -> None:
    udir = os.path.join(args.prefix, 'user')
    if is_done(udir):
        return

    logging.info(f'Building user venv {udir}...')

    python_version = os.environ['R8_PYTHON_VERSION']
    torch_version = os.environ['R8_TORCH_VERSION']
    cuda_version = os.environ['R8_CUDA_VERSION']

    uv = os.path.join(args.prefix, 'bin', 'uv')

    cdir = os.path.realpath(os.path.join(args.prefix, 'cog', 'latest'))
    vdir = os.path.realpath(os.path.join(cdir, f'default-python{python_version}'))
    logging.info(f'Freezing Cog venv {vdir}...')
    cog_req = freeze(uv, vdir)
    with open(os.path.join(args.prefix, 'requirements-cog.txt'), 'w') as f:
        f.write(cog_req)
    cog_versions = parse_requirements(cog_req)

    gdir = os.path.realpath(os.path.join(args.prefix, 'monobase', 'latest'))
    venv = f'python{python_version}-torch{torch_version}-{cuda_suffix(cuda_version)}'
    vdir = os.path.join(gdir, venv)
    logging.info(f'Freezing monobase venv {vdir}...')
    mono_req = freeze(uv, vdir)
    with open(os.path.join(args.prefix, 'requirements-mono.txt'), 'w') as f:
        f.write(cog_req)
    mono_versions = parse_requirements(mono_req)

    logging.info(f'Creating user venv {udir}...')
    cmd = ['uv', 'venv', '--python', python_version, udir]
    subprocess.run(cmd, check=True)

    logging.info(f'Compiling user {args.requirements}...')
    cmd = [uv, 'pip', 'compile', '--python-platform', 'x86_64-unknown-linux-gnu']
    cmd = cmd + [args.requirements]
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = udir
    try:
        proc = subprocess.run(cmd, check=True, env=env, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logging.error(e.stdout)
        logging.error(e.stderr)
        raise e

    # FIXME: remove user package already in mono_versions
    # FIXME: support @ and other requirement specs
    user_req = proc.stdout
    user_req_path = os.path.join(args.prefix, 'requirements-user.txt')
    with open(user_req_path, 'w') as f:
        f.write(user_req)
    user_versions = parse_requirements(user_req)
    keys = set(
        list(cog_versions.keys())
        + list(mono_versions.keys())
        + list(user_versions.keys())
    )
    for k in keys:
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
        if len(majors) == 1 and len(minors) == 1:
            continue
        elif len(majors) == 1 and len(minors) > 1:
            logging.warning(
                f'possible incompatible versions for {k}: cog=={cvs}, mono=={mvs}, user=={uvs}'
            )
        elif len(majors) > 1 and len(minors) > 1:
            logging.error(
                f'probable incompatible versions for {k}: cog=={cvs}, mono=={mvs}, user=={uvs}'
            )

    cmd = [uv, 'pip', 'install', '--no-deps', '--requirement', user_req_path]
    subprocess.run(cmd, check=True, env=env)

    mark_done(udir)
    logging.info(f'User venv installed in {udir}')
