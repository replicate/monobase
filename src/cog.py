import argparse
import logging
import os.path
import re
import shutil
import subprocess

import requests

from monogen import MONOGENS
from util import Version, is_done, mark_done

LINK_REGEX = re.compile(r'<(?P<url>https://[^>]+)>; rel="next"')
MIN_COG_VERSION = Version.parse('0.9.26')


def get_cog_versions() -> list[Version]:
    logging.info('Getting cog versions...')
    url = 'https://api.github.com/repos/replicate/cog/releases'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    versions = []

    while True:
        resp = requests.get(url, headers)
        resp.raise_for_status()
        for r in resp.json():
            vs = r['name'].lstrip('v')
            v = Version.parse(vs)
            if vs.startswith('0.10.'):
                continue
            if v < MIN_COG_VERSION:
                continue
            versions.append(v)

        m = LINK_REGEX.search(resp.headers.get('link', ''))
        if not m:
            break
        url = m.group('url')
    versions = sorted(versions, reverse=True)
    logging.info(f'Cog versions: {versions}')
    return versions


def get_python_versions(args: argparse.Namespace) -> list[str]:
    versions = []
    for mg in MONOGENS[args.environment]:
        versions += map(Version.parse, mg.python.keys())
    return sorted(set(versions), reverse=True)


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

    # Create venvs with Python major.minor only
    # Since we only the site-packages, not Python interpreters
    uv = os.path.join(args.prefix, 'bin', 'uv')
    for p in get_python_versions(args):
        for c in get_cog_versions():
            venv = f'python{p}-cog{c}'
            vdir = os.path.join(gdir, venv)
            cmd = [uv, 'venv', '--python', str(p), vdir]
            subprocess.run(cmd, check=True)

            env = os.environ.copy()
            env['VIRTUAL_ENV'] = vdir
            cmd = [uv, 'pip', 'install', f'cog=={c}']
            subprocess.run(cmd, check=True, env=env)
    mark_done(gdir)

    latest = os.path.join(cdir, 'latest')
    if os.path.exists(latest):
        os.remove(latest)
    os.symlink(f'g{gid:05d}', latest)

    for g in prev:
        logging.info(f'Deleting previous cog generation in {g}...')
        shutil.rmtree(g, ignore_errors=True)
