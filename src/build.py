import argparse
import os
import os.path
import re
import subprocess
import sys

from monogen import MONOGENS, MonoGen
from cuda import install_cuda, install_cudnn
from optimize import optimize_ld_cache, optimize_rdfind
from prune import clean_uv_cache, prune_cuda, prune_old_gen, prune_uv_cache
from util import Version, is_done, logger, mark_done
from uv import install_venv


parser = argparse.ArgumentParser(description='Build monobase enviroment')
parser.add_argument('--environment', metavar='ENV', default='prod', choices=['test', 'prod'],
                    help='environment [test, prod], default=prod')
parser.add_argument('--min-gen-id', metavar='N', type=int, default=0,
                    help='minimum generation ID, default=0')
parser.add_argument('--max-gen-id', metavar='N', type=int, default=sys.maxsize,
                    help='maximum generation ID, default=inf')
parser.add_argument('--prefix', metavar='PATH', default='/usr/local',
                    help='prefix for monobase')
parser.add_argument('--cache', metavar='PATH', default='/var/cache/monobase',
                    help='cache for monobase')
parser.add_argument('--prune-old-gen', default=False, action='store_true',
                    help='prune old generations')
parser.add_argument('--prune-cuda', default=False, action='store_true',
                    help='prune unused CUDAs and CuDNNs')
parser.add_argument('--prune-uv-cache', default=True, action='store_true',
                    help='prune uv cache')
parser.add_argument('--clean-uv-cache', default=False, action='store_true',
                    help='clean uv cache')


def build_generation(args: argparse.Namespace, mg: MonoGen) -> None:
    gdir = os.path.join(args.prefix, 'monobase', 'g%05d' % mg.id)
    if is_done(gdir):
        return

    logger.info(f'Building monobase generation {mg.id}...')
    os.makedirs(gdir, exist_ok=True)

    for k, v in sorted(mg.cuda.items(), key=lambda kv: Version.parse(kv[0]), reverse=True):
        src = install_cuda(args, v)
        dst = f'{gdir}/cuda{k}'
        os.symlink(os.path.relpath(src, gdir), dst)
        logger.info(f'CUDA symlinked in {dst}')

    cuda_major_p = re.compile(r'\.\d+$')
    cuda_majors = set(cuda_major_p.sub('', k) for k in mg.cuda.keys())
    for k, v in sorted(mg.cudnn.items(), key=lambda kv: Version.parse(kv[0]), reverse=True):
        for m in sorted(cuda_majors, key=Version.parse, reverse=True):
            src = install_cudnn(args, v, m)
            dst = f'{gdir}/cudnn{k}-cuda{m}'
            os.symlink(os.path.relpath(src, gdir), dst)
            logger.info(f'CuDNN symlinked in {dst}')

    suffix = '' if args.environment == 'prod' else f'-{args.environment}'
    rdir = os.path.join('/srv/r8/monobase', f'requirements{suffix}', 'g%05d' % mg.id)
    for p, pf in sorted(mg.python.items(), key=lambda kv: Version.parse(kv[0]), reverse=True):
        for t in sorted(mg.torch, key=Version.parse, reverse=True):
            for c in sorted(mg.cuda.keys(), key=Version.parse, reverse=True):
                install_venv(args, rdir, gdir, p, pf, t, c)

    optimize_ld_cache(args, gdir, mg)
    optimize_rdfind(args, gdir, mg)

    mark_done(gdir)
    logger.info(f'Generation {mg.id} installed in {gdir}')


def build(args: argparse.Namespace) -> None:
    os.makedirs(args.cache, exist_ok=True)

    for mg in sorted(MONOGENS[args.environment], reverse=True):
        if mg.id < args.min_gen_id or mg.id > args.max_gen_id:
            continue
        build_generation(args, mg)

    if args.prune_old_gen:
        prune_old_gen(args.min_gen_id)
    if args.prune_cuda:
        prune_cuda()
    if args.prune_uv_cache:
        prune_uv_cache()
    if args.clean_uv_cache:
        clean_uv_cache()

    logger.info(f'Calculating disk usage in {args.prefix}...')
    cmd = ['du', '-ch', '-d', '1', args.prefix]
    subprocess.run(cmd, check=True)

    logger.info('Monobase build completed')
    mark_done('/srv/r8/monobase')


if __name__ == '__main__':
    args = parser.parse_args()
    build(args)
