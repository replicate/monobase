import argparse
import os
import re
import subprocess

from monogen import MonoGen
from util import logger


def optimize_ld_cache(args: argparse.Namespace, gdir: str, mg: MonoGen) -> None:
    logger.info(f'Generating ld.so.cache for generation {mg.id}...')
    cuda_major_p = re.compile(r'\.\d+$')
    for cuda in mg.cuda.keys():
        for cudnn in mg.cudnn.keys():
            for python, python_full in mg.python.items():
                k = f'cuda{cuda}-cudnn{cudnn}-python{python}'
                dirs = [
                    f'{gdir}/cuda{cuda}/lib64',
                    f'{gdir}/cudnn{cudnn}-cuda{cuda_major_p.sub('', cuda)}/lib',
                    f'{args.prefix}/uv/python/cpython-{python_full}-linux-x86_64-gnu/lib',
                ]
                cache_dir = f'{gdir}/ld.so.cache.d'
                os.makedirs(cache_dir, exist_ok=True)
                cmd = ['ldconfig', '-C', f'{cache_dir}/{k}'] + dirs
                subprocess.run(cmd, check=True)


def optimize_rdfind(args: argparse.Namespace, gdir: str, mg: MonoGen) -> None:
    logger.info(f'Running rdfind for generation {mg.id}...')
    cmd = [
        'rdfind', '-minsize', str(1024*1024),
        '-deterministic', 'true',
        '-makehardlinks', 'true',
        '-outputname', '/dev/null',
        f'{args.prefix}/uv/cache',
        f'{args.prefix}/cuda',
        gdir,
    ]
    subprocess.run(cmd, check=True)
