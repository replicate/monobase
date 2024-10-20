import argparse
import hashlib
import json
import logging
import os.path
import re
import shutil
import subprocess
from typing import Optional

from monogen import MONOGENS
from util import Version, is_done, mark_done

LINK_REGEX = re.compile(r'<(?P<url>https://[^>]+)>; rel="next"')
MIN_COG_VERSION = Version.parse('0.9.26')

# Cog version to requirement specifier mapping
COG_VERSIONS = {
    # Releases
    '0.9.26': None,
    '0.11.1': None,
    # Wait for COG_WAIT_FILE
    '00b98bc9': 'cog @ https://github.com/replicate/cog/archive/00b98bc90bb784102243b7aec41ad1cbffaefece.zip',
}
DEFAULT_COG_VERSION = '00b98bc9'


def cog_gen_hash(
    cog_versions: dict[str, Optional[str]],
    default_cog_version: str,
    python_versions: list[str],
) -> str:
    j = {
        'cog_versions': cog_versions,
        'default_cog_version': default_cog_version,
        'python_versions': python_versions,
    }
    return hashlib.sha256(json.dumps(j).encode('utf-8')).hexdigest()


def get_python_versions(args: argparse.Namespace) -> list[str]:
    versions: list[Version] = []
    for mg in MONOGENS[args.environment]:
        versions += map(Version.parse, mg.python.keys())
    return list(map(str, sorted(set(versions), reverse=True)))


def install_cog(
    uv: str, gdir: str, cog_version: str, cog_req: str, python_version: str
) -> None:
    venv = f'cog{cog_version}-python{python_version}'
    vdir = os.path.join(gdir, venv)
    cmd = [uv, 'venv', '--python', python_version, vdir]
    subprocess.run(cmd, check=True)

    env = os.environ.copy()
    env['VIRTUAL_ENV'] = vdir
    cmd = [uv, 'pip', 'install', cog_req]
    subprocess.run(cmd, check=True, env=env)

    if cog_version == DEFAULT_COG_VERSION:
        default = os.path.join(gdir, f'default-python{python_version}')
        if os.path.exists(default):
            os.remove(default)
        os.symlink(venv, default)


def install_cogs(args: argparse.Namespace) -> None:
    cdir = os.path.join(args.prefix, 'cog')
    os.makedirs(cdir, exist_ok=True)

    # Consistent hash of Cog versions as generation ID
    python_versions = get_python_versions(args)
    sha256 = cog_gen_hash(COG_VERSIONS, DEFAULT_COG_VERSION, python_versions)[:8]
    gid = f'g{sha256}'
    gdir = os.path.join(cdir, gid)
    if is_done(gdir):
        return

    logging.info(f'Installing cog generation {gid} in {gdir}...')

    # Cog * Python because Python version is required for venvs
    # And Cog transitives may be Python version dependent
    # Create venvs with Python major.minor only
    # Since we only the site-packages, not Python interpreters
    uv = os.path.join(args.prefix, 'bin', 'uv')
    for c, req in COG_VERSIONS.items():
        if req is None:
            req = f'cog=={c}'
        for p in python_versions:
            install_cog(uv, gdir, c, req, p)

    latest = os.path.join(cdir, 'latest')
    if os.path.exists(latest):
        os.remove(latest)
    os.symlink(gid, latest)

    mark_done(gdir)

    for g in os.listdir(cdir):
        if g in {'latest', gid}:
            continue
        logging.info(f'Deleting previous cog generation in {g}...')
        shutil.rmtree(os.path.join(cdir, g), ignore_errors=True)
