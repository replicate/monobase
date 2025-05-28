import argparse
import logging
import os.path
import shutil
import subprocess

log = logging.getLogger(__name__)


def prune_old_gen(args: argparse.Namespace) -> None:
    for gid in range(args.min_gen_id):
        gdir = os.path.join(args.prefix, 'monobase', f'g{gid:05d}')
        if os.path.exists(gdir):
            log.info(f'Pruning old generation {gid} in {gdir}')
            shutil.rmtree(gdir, ignore_errors=True)


def prune_cuda(args: argparse.Namespace) -> None:
    cmd = [
        'find',
        f'{args.prefix}/monobase',
        '-type',
        'l',
        '-maxdepth',
        '2',
        '(',
        '-name',
        'cuda*',
        '-or',
        '-name',
        'cudnn*',
        ')',
        '-print0',
    ]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    links = set(filter(None, proc.stdout.split('\0')))
    sources = set(map(os.path.realpath, links))

    cdir = os.path.join(args.prefix, 'cuda')
    prefixes = {'cuda', 'cudnn'}
    for e in os.listdir(cdir):
        prefix = e.split('-')[0]
        if prefix not in prefixes:
            continue

        src = os.path.join(cdir, e)
        if src not in sources:
            log.info(f'Pruning unused {prefix} in {src}...')
            shutil.rmtree(src, ignore_errors=True)


def prune_uv_cache() -> None:
    log.info('Pruning uv cache...')
    cmd = ['uv', 'cache', 'prune']
    subprocess.run(cmd, check=True)


def clean_uv_cache() -> None:
    log.info('Cleaning uv cache...')
    cmd = ['uv', 'cache', 'clean']
    subprocess.run(cmd, check=True)
