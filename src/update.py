from tempfile import TemporaryDirectory
import argparse
import os.path
import sys

from monogen import MONOGENS, MonoGen
from util import logger
from uv import update_venv

parser = argparse.ArgumentParser(description='Update monobase requirements')
parser.add_argument('--environment', metavar='ENV', default='prod', choices=['test', 'prod'],
                    help='environment [test, prod], default=prod')
parser.add_argument('--min-gen-id', metavar='N', type=int, default=0,
                    help='minimum generation ID, default=0')
parser.add_argument('--max-gen-id', metavar='N', type=int, default=sys.maxsize,
                    help='maximum generation ID, default=inf')


def update_generation(args: argparse.Namespace, tmp: TemporaryDirectory, mg: MonoGen) -> None:
    logger.info(f'Updating monobase generation {mg.id}')
    suffix = '' if args.environment == 'prod' else f'-{args.environment}'
    rdir = os.path.join(os.path.dirname(__file__), f'requirements{suffix}', 'g%05d' % mg.id)
    os.makedirs(rdir, exist_ok=True)

    for p in mg.python:
        for t in mg.torch:
            for c in mg.cuda.keys():
                update_venv(rdir, tmp.name, p, t, c, mg.pip_pkgs)


def update(args: argparse.Namespace) -> None:
    tmp = TemporaryDirectory(prefix='monobase-')
    for mg in MONOGENS[args.environment]:
        if mg.id < args.min_gen_id or mg.id > args.max_gen_id:
            continue
        update_generation(args, tmp, mg)


if __name__ == '__main__':
    args = parser.parse_args()
    update(args)
