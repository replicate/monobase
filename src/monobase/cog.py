import argparse
import hashlib
import itertools
import json
import logging
import os.path
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

from monobase.util import Version, mark_done, require_done_or_rm

LINK_REGEX = re.compile(r'<(?P<url>https://[^>]+)>; rel="next"')

log = logging.getLogger(__name__)

# CDN for matrix.json with version & URL for custom packages, e.g. coglet, hf_transfer
# To work around GitHub rate limit
matrx_json_url = 'https://monobase-packages.replicate.delivery/matrix.json'
matrix = json.loads(urllib.request.urlopen(matrx_json_url).read())


def hash_str(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def get_coglet_release(part: str) -> dict[str, Any]:
    if part == 'latest':
        return matrix['latest_coglet']
    url = f'https://api.github.com/repos/replicate/cog-runtime/releases/{part}'
    content = urllib.request.urlopen(url).read()
    blob = json.loads(content)
    return {'version': blob['name'], 'url': blob['assets'][0]['browser_download_url']}


def cog_gen_hash(
    cog_versions: list[str],
    default_cog_version: str,
    python_versions: list[str],
) -> str:
    cvs = []
    for cv in cog_versions:
        # Hash actual coglet version instead of 'coglet'
        # So that new releases trigger hash change and re-install
        if cv == 'coglet':
            v = get_coglet_release('latest')['version']
            cv = f'coglet=={v}'
        cvs.append(cv)
    j = {
        'cog_versions': cvs,
        'default_cog_version': default_cog_version,
        'python_versions': python_versions,
    }
    return hash_str(json.dumps(j))


def install_cog(
    uv: str,
    gdir: str,
    cog_version: str,
    is_default: bool,
    python_version: str,
    python_full_version: str,
    extra_packages: list[str],
) -> None:
    if cog_version.startswith('https://') or cog_version.startswith('file://'):
        h = hash_str(cog_version)[:8]
        pkg = 'coglet' if 'coglet' in cog_version else 'cog'
        cog_name = f'{pkg}{h}'
        spec = f'{pkg}@{cog_version}'
    elif cog_version.startswith('coglet'):
        if python_version == '3.8':
            log.warning('cog-runtime does not support Python 3.8')
            return
        try:
            if cog_version == 'coglet':
                v = 'latest'
                part = 'latest'
            elif '==' in cog_version:
                v = cog_version.split('==')[1].strip()
                part = f'tags/v{v}'
            else:
                log.error(f'Unsupported cog version {cog_version}')
                return
            cog_name = f'coglet{v}'
            release = get_coglet_release(part)
            spec = f'coglet@{release["url"]}'
        except Exception as e:
            log.error('Failed to fetch cog-runtime assets: %s', e)
            return
    else:
        cog_name = f'cog{cog_version}'
        spec = f'cog=={cog_version}'

    venv = f'{cog_name}-python{python_version}'
    vdir = os.path.join(gdir, venv)
    cmd = [uv, 'venv', '--python', python_full_version, vdir]
    subprocess.run(cmd, check=True)

    env = os.environ.copy()
    env['VIRTUAL_ENV'] = vdir

    cmd = [
        uv,
        'pip',
        'install',
        '--no-cache',
        '--compile-bytecode',
        spec,
    ] + extra_packages
    subprocess.run(cmd, check=True, env=env)

    # Some predictor code checks for Cog version via importlib.metadata.version("cog")
    # Create cog-*.dist-info/METADATA to support this
    if cog_name.startswith('coglet'):
        sp = os.path.join(vdir, 'lib', f'python{python_version}', 'site-packages')
        # There should only be one glob match
        for src in Path(sp).glob('coglet-*.dist-info'):
            dst = src.parent / src.name.replace('coglet', 'cog', 1)
            dst.mkdir(parents=True, exist_ok=True)
            md = (src / 'METADATA').open().read()
            # "Name: coglet" is usually the 2nd line
            md = md.replace('\nName: coglet\n', '\nName: cog\n')
            (dst / 'METADATA').write_text(md, encoding='utf-8')

    if is_default:
        default = os.path.join(gdir, f'default-python{python_version}')
        if os.path.exists(default):
            os.remove(default)
        os.symlink(venv, default)


def install_cogs(args: argparse.Namespace, python_versions: list[str]) -> None:
    cdir = os.path.join(args.prefix, 'cog')
    os.makedirs(cdir, exist_ok=True)

    # Consistent hash of Cog versions as generation ID
    pvs = list(map(Version.parse, python_versions))
    cog_versions = sorted(set(args.cog_versions))
    sha256 = cog_gen_hash(
        cog_versions, args.default_cog_version, sorted(python_versions)
    )[:8]
    gid = f'g{sha256}'
    gdir = os.path.join(cdir, gid)

    if require_done_or_rm(gdir):
        log.info(f'Cog generation {gid} is complete')
        return

    log.info(f'Installing cog generation {gid} in {gdir}...')

    # Cog * Python because Python version is required for venvs
    # And Cog transitives may be Python version dependent
    # Create venvs with Python major.minor only
    # Since we only the site-packages, not Python interpreters
    uv = os.path.join(args.prefix, 'bin', 'uv')

    hf_transfer = f'hf_transfer@{matrix["latest_hf_transfer"]["url"]}'

    for c, pv in itertools.product(cog_versions, pvs):
        is_default = c == args.default_cog_version
        v = f'{pv.major}.{pv.minor}'
        install_cog(uv, gdir, c, is_default, v, str(pv), [hf_transfer])

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
