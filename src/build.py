import argparse
import logging
import os
import os.path
import re
import subprocess

from cog import install_cogs
from cuda import install_cuda, install_cudnn
from monogen import MONOGENS, MonoGen
from optimize import optimize_ld_cache, optimize_rdfind
from prune import clean_uv_cache, prune_cuda, prune_old_gen, prune_uv_cache
from util import (
    Version,
    add_arguments,
    desc_version,
    desc_version_key,
    is_done,
    mark_done,
    setup_logging,
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
    '--cog-versions',
    metavar='VERSION',
    nargs='+',
    type=str,
    help='Cog versions, x.y.z or GitHub URL',
)
parser.add_argument(
    '--default-cog-version',
    metavar='VERSION',
    help='Default Cog version, x.y.z or GitHub URL',
)
parser.add_argument(
    '--mini',
    default=False,
    action='store_true',
    help='Build a mini mono of 1 generation * 1 venv',
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
    gdir = os.path.join(args.prefix, 'monobase', f'g{mg.id:05d}')
    if is_done(gdir):
        return

    logging.info(f'Building monobase generation {mg.id}...')
    os.makedirs(gdir, exist_ok=True)

    for k, v in desc_version_key(mg.cuda):
        src = install_cuda(args, v)
        dst = f'{gdir}/cuda{k}'
        os.symlink(os.path.relpath(src, gdir), dst)
        logging.info(f'CUDA symlinked in {dst}')

    cuda_major_p = re.compile(r'\.\d+$')
    cuda_majors = set(cuda_major_p.sub('', k) for k in mg.cuda.keys())
    for k, v in desc_version_key(mg.cudnn):
        for m in desc_version(cuda_majors):
            src = install_cudnn(args, v, m)
            dst = f'{gdir}/cudnn{k}-cuda{m}'
            os.symlink(os.path.relpath(src, gdir), dst)
            logging.info(f'CuDNN symlinked in {dst}')

    suffix = '' if args.environment == 'prod' else f'-{args.environment}'
    rdir = os.path.join('/opt/r8/monobase', f'requirements{suffix}', f'g{mg.id:05d}')
    for p, pf in desc_version_key(mg.python):
        for t in desc_version(mg.torch):
            for c in desc_version(mg.cuda.keys()):
                install_venv(args, rdir, gdir, p, pf, t, c)

    optimize_ld_cache(args, gdir, mg)
    optimize_rdfind(args, gdir, mg)

    mark_done(gdir)
    logging.info(f'Generation {mg.id} installed in {gdir}')


def build(args: argparse.Namespace) -> None:
    monogens = sorted(MONOGENS[args.environment], reverse=True)
    if args.mini:
        mg = monogens[0]

        def assert_env(e: str) -> None:
            assert os.environ.get(e) is not None, f'{e} is required for mini mono'

        assert_env('R8_COG_VERSION')
        assert_env('R8_CUDA_VERSION')
        assert_env('R8_CUDNN_VERSION')
        assert_env('R8_PYTHON_VERSION')
        assert_env('R8_TORCH_VERSION')

        assert (
            args.cog_versions is None
        ), 'Mini mono and --cog-versions are mutually exclusive'
        assert (
            args.default_cog_version is None
        ), 'Mini mono and --default-cog-version are mutually exclusive'
        args.cog_versions = [os.environ['R8_COG_VERSION']]
        args.default_cog_version = os.environ['R8_COG_VERSION']

        def pick(d: dict[str, str], env: str) -> dict[str, str]:
            key = os.environ[env]
            return {key: d[key]}

        monogens = [
            MonoGen(
                id=mg.id,
                cuda=pick(mg.cuda, 'R8_CUDA_VERSION'),
                cudnn=pick(mg.cudnn, 'R8_CUDNN_VERSION'),
                python=pick(mg.python, 'R8_PYTHON_VERSION'),
                torch=[os.environ['R8_TORCH_VERSION']],
                pip_pkgs=mg.pip_pkgs,
            )
        ]

    if args.default_cog_version is None:
        assert len(args.cog_versions) == 1, 'Missing --default-cog-version'
        args.default_cog_version = args.cog_versions[0]
    assert (
        args.default_cog_version in args.cog_versions
    ), f'Default Cog {args.default_cog_version} not in {args.cog_versions}'

    os.makedirs(args.cache, exist_ok=True)

    if args.clean_uv_cache:
        clean_uv_cache()

    pvs: list[Version] = []
    for mg in monogens:
        pvs += map(Version.parse, mg.python.keys())
    python_versions = list(map(str, sorted(set(pvs), reverse=True)))
    install_cogs(args, python_versions)

    gens = []
    for i, mg in enumerate(monogens):
        if mg.id < args.min_gen_id or mg.id > args.max_gen_id:
            continue
        build_generation(args, mg)
        gens.append(mg.id)

        if i == 0:
            latest = os.path.join(args.prefix, 'monobase', 'latest')
            if os.path.exists(latest):
                os.remove(latest)
            os.symlink(f'g{mg.id:05d}', latest)

    if args.prune_old_gen:
        prune_old_gen(args)
    if args.prune_cuda:
        prune_cuda(args)
    if args.prune_uv_cache:
        prune_uv_cache()

    logging.info(f'Calculating disk usage in {args.prefix}...')
    cmd = ['du', '-ch', '-d', '1', args.prefix]
    subprocess.run(cmd, check=True)

    logging.info(f'Monobase build completed: {sorted(gens)}')


if __name__ == '__main__':
    setup_logging()
    build(parser.parse_args())
