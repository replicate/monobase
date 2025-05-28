import argparse
import itertools
import logging
import os
import re
import subprocess

from monobase.monogen import MonoGen

log = logging.getLogger(__name__)


def optimize_ld_cache(args: argparse.Namespace, gdir: str, mg: MonoGen) -> None:
    log.info(f'Generating ld.so.cache for generation {mg.id}...')
    cuda_major_p = re.compile(r'\.\d+$')
    for cuda, cudnn, (python, python_full) in itertools.product(
        mg.cuda.keys(),
        mg.cudnn.keys(),
        mg.python.items(),
    ):
        k = f'cuda{cuda}-cudnn{cudnn}-python{python}'

        dirs = [
            f'{gdir}/cuda{cuda}/lib64',
            f'{gdir}/cudnn{cudnn}-cuda{cuda_major_p.sub("", cuda)}/lib',
            f'{args.prefix}/uv/python/cpython-{python_full}-linux-x86_64-gnu/lib',
        ]

        cache_dir = os.path.join(gdir, 'ld.so.cache.d')
        os.makedirs(cache_dir, exist_ok=True)
        cmd = ['ldconfig', '-C', f'{cache_dir}/{k}'] + dirs
        subprocess.run(cmd, check=True)


def optimize_rdfind(args: argparse.Namespace, gdir: str, mg: MonoGen) -> None:
    all_dirs = [
        f'{args.prefix}/uv/cache',
        f'{args.prefix}/cuda',
        gdir,
    ]
    minsize = str(1024 * 1024)

    log.info(f'Running rdfind for generation {mg.id}...')
    cmd = [
        'rdfind',
        '-minsize',
        minsize,
        '-deterministic',
        'true',
        '-makehardlinks',
        'true',
        '-outputname',
        '/dev/null',
        *all_dirs,
    ]
    subprocess.run(cmd, check=True)
