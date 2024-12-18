import argparse
import hashlib
import itertools
import json
import logging
import os.path
import re
import shutil
import subprocess

from opentelemetry import trace

from monobase.util import mark_done, require_done_or_rm, tracer

LINK_REGEX = re.compile(r'<(?P<url>https://[^>]+)>; rel="next"')

log = logging.getLogger(__name__)


def hash_str(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def cog_gen_hash(
    cog_versions: list[str],
    default_cog_version: str,
    python_versions: list[str],
) -> str:
    j = {
        'cog_versions': cog_versions,
        'default_cog_version': default_cog_version,
        'python_versions': python_versions,
    }
    return hash_str(json.dumps(j))


@tracer.start_as_current_span('install_cog')
def install_cog(
    uv: str, gdir: str, cog_version: str, is_default: bool, python_version: str
) -> None:
    trace.get_current_span().set_attributes(
        {
            'uv': uv,
            'cog_version': cog_version,
            'cog_version_is_default': str(is_default),
            'python_version': python_version,
        }
    )

    if cog_version.startswith('https://'):
        name = hash_str(cog_version)[:8]
        spec = f'cog@{cog_version}'
    else:
        name = cog_version
        spec = f'cog=={cog_version}'

    venv = f'cog{name}-python{python_version}'
    vdir = os.path.join(gdir, venv)
    cmd = [uv, 'venv', '--python', python_version, vdir]
    subprocess.run(cmd, check=True)

    env = os.environ.copy()
    env['VIRTUAL_ENV'] = vdir

    cmd = [uv, 'pip', 'install', spec]
    subprocess.run(cmd, check=True, env=env)

    if is_default:
        default = os.path.join(gdir, f'default-python{python_version}')
        if os.path.exists(default):
            os.remove(default)
        os.symlink(venv, default)


@tracer.start_as_current_span('install_cogs')
def install_cogs(args: argparse.Namespace, python_versions: list[str]) -> None:
    cdir = os.path.join(args.prefix, 'cog')
    os.makedirs(cdir, exist_ok=True)

    # Consistent hash of Cog versions as generation ID
    cog_versions = sorted(set(args.cog_versions))
    sha256 = cog_gen_hash(cog_versions, args.default_cog_version, python_versions)[:8]
    gid = f'g{sha256}'
    gdir = os.path.join(cdir, gid)

    trace.get_current_span().set_attributes(
        {
            'generation_id': gid,
            'cog_versions': str(cog_versions),
        }
    )

    if require_done_or_rm(gdir):
        log.info(f'Cog generation {gid} is complete')
        return

    log.info(f'Installing cog generation {gid} in {gdir}...')

    # Cog * Python because Python version is required for venvs
    # And Cog transitives may be Python version dependent
    # Create venvs with Python major.minor only
    # Since we only the site-packages, not Python interpreters
    uv = os.path.join(args.prefix, 'bin', 'uv')

    for c, p in itertools.product(cog_versions, python_versions):
        install_cog(uv, gdir, c, c == args.default_cog_version, p)

    latest = os.path.join(cdir, 'latest')
    if os.path.exists(latest):
        os.remove(latest)
    os.symlink(gid, latest)

    mark_done(
        gdir,
        kind='cog',
        id=gid,
        versions=cog_versions,
        default_version=args.default_cog_version,
        python_versions=python_versions,
    )

    for g in os.listdir(cdir):
        if g in {'latest', gid}:
            continue
        log.info(f'Deleting previous cog generation in {g}...')
        shutil.rmtree(os.path.join(cdir, g), ignore_errors=True)
