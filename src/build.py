import argparse
import os
import os.path
import re
import subprocess

from monogen import MONOGENS, MonoGen
from cuda import install_cuda, install_cudnn
from optimize import optimize_ld_cache, optimize_rdfind
from prune import clean_uv_cache, prune_cuda, prune_old_gen, prune_uv_cache
from util import (
    add_arguments,
    desc_version,
    desc_version_key,
    is_done,
    logger,
    mark_done,
)
from uv import install_venv

parser = argparse.ArgumentParser(description='Build monobase enviroment')
add_arguments(parser)
parser.add_argument(
    '--prefix', metavar='PATH', default='/srv/r8/monobase', help='prefix for monobase'
)
parser.add_argument(
    '--cache', metavar='PATH', default='/var/cache/monobase', help='cache for monobase'
)
parser.add_argument(
    '--prune-old-gen', default=False, action='store_true', help='prune old generations'
)
parser.add_argument(
    '--prune-cuda',
    default=False,
    action='store_true',
    help='prune unused CUDAs and CuDNNs',
)
parser.add_argument(
    '--prune-uv-cache', default=True, action='store_true', help='prune uv cache'
)
parser.add_argument(
    '--clean-uv-cache', default=False, action='store_true', help='clean uv cache'
)


def build_generation(args: argparse.Namespace, mg: MonoGen) -> None:
    gdir = os.path.join(args.prefix, 'monobase', 'g%05d' % mg.id)
    if is_done(gdir):
        return

    logger.info(f'Building monobase generation {mg.id}...')
    os.makedirs(gdir, exist_ok=True)

    for k, v in desc_version_key(mg.cuda):
        src = install_cuda(args, v)
        dst = f'{gdir}/cuda{k}'
        os.symlink(os.path.relpath(src, gdir), dst)
        logger.info(f'CUDA symlinked in {dst}')

    cuda_major_p = re.compile(r'\.\d+$')
    cuda_majors = set(cuda_major_p.sub('', k) for k in mg.cuda.keys())
    for k, v in desc_version_key(mg.cudnn):
        for m in desc_version(cuda_majors):
            src = install_cudnn(args, v, m)
            dst = f'{gdir}/cudnn{k}-cuda{m}'
            os.symlink(os.path.relpath(src, gdir), dst)
            logger.info(f'CuDNN symlinked in {dst}')

    suffix = '' if args.environment == 'prod' else f'-{args.environment}'
    rdir = os.path.join('/opt/r8/monobase', f'requirements{suffix}', 'g%05d' % mg.id)
    for p, pf in desc_version_key(mg.python):
        for t in desc_version(mg.torch):
            for c in desc_version(mg.cuda.keys()):
                install_venv(args, rdir, gdir, p, pf, t, c)

    optimize_ld_cache(args, gdir, mg)
    optimize_rdfind(args, gdir, mg)

    mark_done(gdir)
    logger.info(f'Generation {mg.id} installed in {gdir}')


def build(args: argparse.Namespace) -> None:
    os.makedirs(args.cache, exist_ok=True)

    gens = []
    for mg in sorted(MONOGENS[args.environment], reverse=True):
        if mg.id < args.min_gen_id or mg.id > args.max_gen_id:
            continue
        build_generation(args, mg)
        gens.append(mg.id)

    if args.prune_old_gen:
        prune_old_gen(args)
    if args.prune_cuda:
        prune_cuda(args)
    if args.prune_uv_cache:
        prune_uv_cache()
    if args.clean_uv_cache:
        clean_uv_cache()

    logger.info(f'Calculating disk usage in {args.prefix}...')
    cmd = ['du', '-ch', '-d', '1', args.prefix]
    subprocess.run(cmd, check=True)

    logger.info(f'Monobase build completed: {sorted(gens)}')


if __name__ == '__main__':
    build(parser.parse_args())
