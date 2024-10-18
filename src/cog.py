import argparse
import logging
import os.path
import re
import shutil
import subprocess

import requests

from monogen import MONOGENS
from util import Version, desc_version_key, is_done, mark_done

LINK_REGEX = re.compile(r'<(?P<url>https://[^>]+)>; rel="next"')
MIN_COG_VERSION = Version.parse('0.9.26')

EXTRA_COG_VERSIONS = {
    # Wait for COG_WAIT_FILE
    '00b98bc9': 'cog @ https://github.com/replicate/cog/archive/00b98bc90bb784102243b7aec41ad1cbffaefece.zip'
}
DEFAULT_COG_VERSION = '00b98bc9'


def get_cog_releases() -> dict[str, str]:
    logging.info('Getting cog releases...')
    url = 'https://api.github.com/repos/replicate/cog/releases'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    releases = {}

    while True:
        resp = requests.get(url, headers)
        resp.raise_for_status()
        for r in resp.json():
            v = r['name'].lstrip('v')
            if v.startswith('0.10.'):
                continue
            if Version.parse(v) < MIN_COG_VERSION:
                continue
            releases[v] = f'cog=={v}'
        m = LINK_REGEX.search(resp.headers.get('link', ''))
        if not m:
            break
        url = m.group('url')

    logging.info(f'Cog releases: {releases}')
    return releases


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

    # Always create a new generation when installing cogs
    gid = -1
    prev = []
    for d in sorted(os.listdir(cdir)):
        p = os.path.join(cdir, d)
        if os.path.isdir(p) and d.startswith('g'):
            if not is_done(p):
                continue
            i = int(d[1:])
            prev.append(p)
            if i > gid:
                gid = i
    gid += 1
    gdir = os.path.join(cdir, f'g{gid:05d}')
    logging.info(f'Installing cog generation {gid} in {gdir}...')

    # Cog * Python because Python version is required for venvs
    # And Cog transitives may be Python version dependent
    # Create venvs with Python major.minor only
    # Since we only the site-packages, not Python interpreters
    uv = os.path.join(args.prefix, 'bin', 'uv')
    pvs = get_python_versions(args)
    for c, req in EXTRA_COG_VERSIONS.items():
        for p in pvs:
            install_cog(uv, gdir, c, req, p)
    for c, req in desc_version_key(get_cog_releases()):
        for p in pvs:
            install_cog(uv, gdir, c, req, p)

    mark_done(gdir)

    latest = os.path.join(cdir, 'latest')
    if os.path.exists(latest):
        os.remove(latest)
    os.symlink(f'g{gid:05d}', latest)

    for g in prev:
        logging.info(f'Deleting previous cog generation in {g}...')
        shutil.rmtree(g, ignore_errors=True)
