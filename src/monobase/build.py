import argparse
import datetime
import itertools
import logging
import os
import os.path
import re

from opentelemetry import trace

from monobase.cog import install_cogs
from monobase.cuda import install_cuda, install_cudnn
from monobase.monogen import MONOGENS, MonoGen
from monobase.optimize import optimize_ld_cache, optimize_rdfind
from monobase.prune import clean_uv_cache, prune_cuda, prune_old_gen, prune_uv_cache
from monobase.user import build_user_venv
from monobase.util import (
    HERE,
    IN_KUBERNETES,
    NODE_FEATURE_LABEL_FILE,
    Version,
    add_arguments,
    desc_version,
    desc_version_key,
    du,
    mark_done,
    require_done_or_rm,
    setup_logging,
    setup_opentelemetry,
    tracer,
)
from monobase.uv import install_venv

log = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description='Build monobase enviroment')
add_arguments(parser)
parser.add_argument(
    '--prefix',
    metavar='PATH',
    default='/srv/r8/monobase',
    help='prefix for monobase',
)
parser.add_argument(
    '--cache',
    metavar='PATH',
    default='/var/cache/monobase',
    help='cache for monobase',
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
    '--requirements',
    metavar='FILE',
    help='Python requirements.txt for user layer',
)
parser.add_argument(
    '--prune-old-gen',
    default=False,
    action='store_true',
    help='prune old generations',
)
parser.add_argument(
    '--skip-cuda',
    default=False,
    action='store_true',
    help='skip CUDAs and CuDNNs',
)
parser.add_argument(
    '--prune-cuda',
    default=False,
    action='store_true',
    help='prune unused CUDAs and CuDNNs',
)
parser.add_argument(
    '--prune-uv-cache',
    default=True,
    action='store_true',
    help='prune uv cache',
)
parser.add_argument(
    '--clean-uv-cache',
    default=False,
    action='store_true',
    help='clean uv cache',
)
parser.add_argument(
    '--all-done-dir',
    default='/srv/r8/monobase',
    help='directory in which to mark the entire build process done',
)
parser.add_argument(
    '--write-node-feature-discovery-labels',
    default=IN_KUBERNETES,
    action='store_true',
    help=f'write labels to {NODE_FEATURE_LABEL_FILE}',
)


@tracer.start_as_current_span('build_generation')
def build_generation(args: argparse.Namespace, mg: MonoGen) -> None:
    span = trace.get_current_span()
    span.set_attributes(mg.otel_attributes)

    gdir = os.path.join(args.prefix, 'monobase', f'g{mg.id:05d}')

    span.set_attribute('generation_dir', gdir)

    if require_done_or_rm(gdir):
        log.info(f'Monobase generation {mg.id} is complete')
        return

    log.info(f'Building monobase generation {mg.id}...')
    os.makedirs(gdir, exist_ok=True)

    for k, v in desc_version_key(mg.cuda):
        src = install_cuda(args, v)
        dst = f'{gdir}/cuda{k}'
        reldst = os.path.relpath(src, gdir)
        if os.path.exists(dst):
            os.remove(dst)
        os.symlink(reldst, dst)
        log.info(f'CUDA symlinked in {dst}')

    cuda_major_p = re.compile(r'\.\d+$')
    cuda_majors = set(cuda_major_p.sub('', k) for k in mg.cuda.keys())
    for (k, v), m in itertools.product(
        desc_version_key(mg.cudnn), desc_version(cuda_majors)
    ):
        src = install_cudnn(args, v, m)
        dst = f'{gdir}/cudnn{k}-cuda{m}'
        reldst = os.path.relpath(src, gdir)
        if os.path.exists(dst):
            os.remove(dst)
        os.symlink(reldst, dst)
        log.info(f'CuDNN symlinked in {dst}')

    suffix = '' if args.environment == 'prod' else f'-{args.environment}'
    rdir = os.path.join(HERE, f'requirements{suffix}', f'g{mg.id:05d}')
    for (p, pf), t, c in itertools.product(
        desc_version_key(mg.python),
        desc_version(mg.torch),
        desc_version(mg.cuda.keys()),
    ):
        install_venv(args, rdir, gdir, p, pf, t, c)

    optimize_ld_cache(args, gdir, mg)
    optimize_rdfind(args, gdir, mg)

    mark_done(gdir, kind='monogen', **mg.__dict__)
    log.info(f'Generation {mg.id} installed in {gdir}')


@tracer.start_as_current_span('build')
def build(args: argparse.Namespace) -> None:
    span = trace.get_current_span()
    span.set_attributes({f'build_{k}': str(v) for k, v in args.__dict__.items()})

    start_time = datetime.datetime.now(datetime.UTC)

    monogens = sorted(MONOGENS[args.environment], reverse=True)
    if args.mini:
        mg = monogens[0]

        def assert_env(e: str) -> None:
            assert os.environ.get(e) is not None, f'{e} is required for mini mono'

        assert_env('R8_COG_VERSION')
        assert_env('R8_PYTHON_VERSION')
        assert_env('R8_TORCH_VERSION')
        if not args.skip_cuda:
            assert_env('R8_CUDA_VERSION')
            assert_env('R8_CUDNN_VERSION')

        assert (
            args.cog_versions is None
        ), 'Mini mono and --cog-versions are mutually exclusive'
        assert (
            args.default_cog_version is None
        ), 'Mini mono and --default-cog-version are mutually exclusive'
        args.cog_versions = [os.environ['R8_COG_VERSION']]
        args.default_cog_version = os.environ['R8_COG_VERSION']

        def pick(
            d: dict[str, str], env: str, fail_on_empty: bool = True
        ) -> dict[str, str]:
            try:
                key = os.environ[env]
                return {key: d[key]}
            except KeyError:
                if fail_on_empty:
                    raise
                return {}

        monogens = [
            MonoGen(
                id=mg.id,
                cuda=pick(mg.cuda, 'R8_CUDA_VERSION', fail_on_empty=not args.skip_cuda),
                cudnn=pick(
                    mg.cudnn, 'R8_CUDNN_VERSION', fail_on_empty=not args.skip_cuda
                ),
                python=pick(mg.python, 'R8_PYTHON_VERSION'),
                torch=[os.environ['R8_TORCH_VERSION']],
                pip_pkgs=mg.pip_pkgs,
            )
        ]
    if args.requirements is not None:
        assert args.mini, 'Mini mono is a prerequisite for --requirements'

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

            if args.write_node_feature_discovery_labels:
                done = datetime.datetime.now(datetime.UTC).strftime('%Y%m%dT%H%M%SZ')

                with open(NODE_FEATURE_LABEL_FILE, 'w') as fp:
                    fp.write(f'done={done}\n')

                os.chmod(NODE_FEATURE_LABEL_FILE, 0o644)

                log.info(f'Wrote done={done} to {NODE_FEATURE_LABEL_FILE}')

    if args.requirements is not None:
        build_user_venv(args)

    if args.prune_old_gen:
        prune_old_gen(args)

    if args.prune_cuda:
        prune_cuda(args)

    if args.prune_uv_cache:
        prune_uv_cache()

    log.info(f'Calculating disk usage in {args.prefix}...')
    du(args.prefix)

    duration = datetime.datetime.now(datetime.UTC) - start_time
    log.info(
        f'Monobase build completed: generations={sorted(gens)} duration={duration}'
    )

    mark_done(args.all_done_dir, kind='build', duration=str(duration), gens=gens)


if __name__ == '__main__':
    setup_logging()
    setup_opentelemetry()
    build(parser.parse_args())
