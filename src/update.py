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

    for p, pf in sorted(mg.python.items(), reverse=True):
        for t in sorted(mg.torch, reverse=True):
            for c in sorted(mg.cuda.keys(), reverse=True):
                update_venv(rdir, tmp.name, p, pf, t, c, mg.pip_pkgs)


def update(args: argparse.Namespace) -> None:
    tmp = TemporaryDirectory(prefix='monobase-')
    for mg in sorted(MONOGENS[args.environment], reverse=True):
        if mg.id < args.min_gen_id or mg.id > args.max_gen_id:
            continue
        update_generation(args, tmp, mg)

    logger.info('Monobase update completed')


if __name__ == '__main__':
    args = parser.parse_args()
    update(args)
